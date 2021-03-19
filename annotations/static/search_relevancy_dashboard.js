var SearchRelevancyApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#search-relevancy-app',
    data: {
        locations: [],
        jobFunctions: [],
        jobFunctionTree: {},
        parent_lookup: {},
        branches: {},
        showPassingChecks: false,
        shades: ['rgb(0,128,66)', 'rgb(49,163,84)', 'rgba(120,198,121)', 'rgb(193,230,153)', 'rgb(255,255,179'],
        searchCases: [],
        collapseNonMatchedResults: true
    },
    mounted: function () {
        d3.json('/annotations/locations').then(
            data => {
                // assuming canonical names of APPROVED locations are unique
                this.locations = data.locations.filter(l=>l.approved)
                })
                this.baseQuery('/job-functions/').then(data => {
                    rooted_tree = {'name': 'All Functions', 'children': data} // this may need changing the API
                    this.jobFunctionTree = d3.hierarchy(rooted_tree)
                    this.treeCheck()
                })
    },
    methods: {
        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
        baseQuery: async function(queryString, result) {
            return d3.json(queryString, {
                method: 'GET',
                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": this.getCookie('csrftoken')
                },
            })
        },

        treeCheck: function() {
            // ensure we only have one root: International
            let locs = this.locations
                .filter(l=>l.mapbox_within__canonical_name !== null || l.canonical_name == "International")
                
            locs.forEach(l=>{ // root cannot be null
                if(l.mapbox_within__canonical_name == null) Vue.delete(l, 'mapbox_within__canonical_name')
            })

            // create location tree
            locationTree = d3.stratify().id(d=>d.canonical_name).parentId(d=>d.mapbox_within__canonical_name)(locs)
            locationTree.each(node=>node.data.name = node.data.canonical_name) // use 'name' for consistency with function tree

            vm = this
           
            linealRelation = function(name_a, name_b, tree) {

                let ancestorOf = function(name_a, name_b, tree) {
                    let ancestor = tree.find(loc=>loc.data.name == name_a)
                    if(!ancestor) {
                        return false
                    }
                    return ancestor.descendants().find(loc => loc.data.name == name_b)
                }
                return ancestorOf(name_a, name_b, tree) || ancestorOf(name_b, name_a, tree)
            }

            const limit = 100
            const checkSearch = function(jobFunction, industry, location) {
                vm.baseQuery(`/products/?includeLocationId=${location.id}&jobFunctionId=${jobFunction.id}&industryId=${industry.id}&limit=${limit}`).then(data => {
                    data.results.forEach((result, resultIndex) => {
                            result.outcomes = {}
                            result.outcomes.locationMatch = result.locations.some(l => linealRelation(location.name, l.canonical_name, locationTree))
                            result.outcomes.functionMatch = result.job_functions.some(f => linealRelation(jobFunction.name, f.name, vm.jobFunctionTree))
                                                            || result.job_functions.length == 0 // until we have global job_function
                    })
                    // add reference results
                    vm.baseQuery(`/annotations/reference_product_search?location_ids=${location.id}&job_function_ids=${jobFunction.id}&industryId=${industry.id}&limit=${limit}`).then(refData => {

                        refData = refData.sort((a,b)=>b.location_specificity - a.location_specificity)
                        vm.searchCases.push({
                            'query': {
                                'location': location,
                                'jobFunction': jobFunction,
                                'industry': industry
                            },
                            'results': data.results,
                            'reference_results': refData
                        })
                    })
                })
            }

            d3.json('/static/data/searchTestCases.json').then(data=>{
                vm.searchCases = []
                data.forEach(c => {
                    checkSearch(c.jobFunction, c.industry, c.location)
                })
            })
        },
        names: function(list) {
            return list.map(e=>e.name ? e.name : e.canonical_name).join(', ')
        },
        missingResult: function(searchCase, refResult) {
            return searchCase && !searchCase.results.some(result=>result.product_id == refResult.product_id)
        }
    }
})