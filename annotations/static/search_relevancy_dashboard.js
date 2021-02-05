var SearchRelevancyApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#search-relevancy-app',
    data: {
        locations: [],
        jobFunctions: [],
        parent_lookup: {},
        branches: {},
        showPassingChecks: false,
        shades: ['rgb(0,128,66)', 'rgb(49,163,84)', 'rgba(120,198,121)', 'rgb(193,230,153)', 'rgb(255,255,179'],
        searchCases: []
    },
    mounted: function () {
        vm = this
        d3.json('/annotations/locations').then(
            data => {
                this.locations = data.locations
                for (loc of this.locations) {
                    if (loc.mapbox_within__mapbox_id != null) {
                        this.parent_lookup[loc.mapbox_id] = loc.mapbox_within__mapbox_id
                    }
                }

                 let ancestors = function(mapbox_id) {
                    let parent_lookup = vm.parent_lookup[mapbox_id]
                    return parent_lookup ? [parent_lookup].concat(ancestors(parent_lookup)) : []
                }

                // once we have complete lookup we can build all branches
                for (loc of vm.locations) {
                    this.branches[loc.mapbox_id] = ancestors(loc.mapbox_id)
                }
            }
        )
        this.searchChecks()

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

        /**
            We check consistency within result set, that all matches for first rule are ranked above all matches for second rule, and so on.
            We don't currently check for missing results or that results match one of the rules.
        */
        searchChecks: function() {
           
            vm = this
           
            const checkSearch = function(jobFunction, industry, location) {

                const GENERIC_INDUSTRY_ID = 29, GLOBAL=2425 // hardcoded from production ids
                const limit = 50

                const matchesFunctionIndustryLocation = function(r) {
                    return idInList(jobFunction.id, r.job_functions)
                        && idInList(location.id, r.locations)
                        && idInList(industry.id, r.industries)
                }
                const matchesFunctionLocation = function(r) {
                    return idInList(jobFunction.id, r.job_functions)
                        && idInList(location.id, r.locations)
                }
                const matchesLocationGeneric = function(r) {
                    return idInList(GENERIC_INDUSTRY_ID, r.industries)
                        && idInList(location.id, r.locations)
                }
                const matchesFunctionGlobally = function(r) {
                    return idInList(GLOBAL, r.locations)
                        && idInList(jobFunction.id, r.job_functions)
                }
                const matchesGenericGlobal = function(r) {
                    return idInList(GENERIC_INDUSTRY_ID, r.industries)
                        && idInList(GLOBAL, r.locations)
                }

                const displayRecord = function(item) {
                    return [item.job_functions.map(e=>e.name).join(), item.industries.map(e=>e.name).join(), item.locations.map(e=>e.canonical_name).join()]
                }

                const idInList = function(id, list) {
                    return list.some(e => e.id == id)
                }    

                const trimRecord = function(item) {
                    delete item.description
                    delete item.duration
                    delete item.cross_postings
                    delete item.logo_url
                    delete item.ratecard_price
                    delete item.vonq_price
                    delete item.time_to_process
                    return item
                }

                vm.baseQuery(`/products/?includeLocationId=${location.id}&jobFunctionId=${jobFunction.id}&industryId=${industry.id}&limit=${limit}`).then(data => {
                    console.log('searching for ', location, jobFunction, industry )
                    console.log(data.results.map(r=>{
                        return displayRecord(r);
                    }))

                    let rules = [
                        {'label': 'match function & industry & location', 'fn': matchesFunctionIndustryLocation}, 
                        {'label': 'match function & location', 'fn': matchesFunctionLocation},
                        {'label': 'match generic board in location', 'fn': matchesLocationGeneric},
                        {'label': 'match function globally', 'fn': matchesFunctionGlobally},
                        {'label': 'match global generic', 'fn': matchesGenericGlobal}
                    ]

                    // annotate results with index of first rule they match
                    data.results.forEach(result=>{
                        result.firstRuleMatch = rules.findIndex(rule=>rule.fn(result))
                    })

                    // find rule boundaries
                    // startsAt and endsBy having same value means the rule is not matched
                    ruleOutcomes = []
                    rules.forEach((rule, ruleIndex)=>{
                        rule.startsAt = ruleIndex == 0 ? 0 : rules[ruleIndex-1].endsBy  // starts where prior rules ends, or 0 for first rule
                        console.log('Checking ' + rule.label + ' from position ' + rule.startsAt + ' ...')
                        let endpoint = rule.startsAt //  update as rule matches for successive results
                        let ended = false
                        let lateMatches = [] // for this rule
                        data.results.forEach((result, resultIndex) => { // examining all results for this rule...
                            if( resultIndex >= rule.startsAt ) { // ...but skipping results matched by prior rules
                                if(! rule.fn(result) ) { // rule does not match result
                                    ended = true;
                                } else if ( ended ) { // 'late' match after rule has stopped matching 
                                    console.log(`ERROR: late match at position ${resultIndex} after rule ended at ${endpoint}:`,  displayRecord(result))
                                    lateMatches.push({'resultIndex': resultIndex, 'endpoint': endpoint, 'result': result})
                                }
                                else { // update endpoint as matching continues
                                    endpoint = resultIndex + 1 // endpoint is after this result
                                    console.log(resultIndex + " : " + displayRecord(result))
                                }
                            }
                        })
                        // endpoint can be beyond last index, i.e. endpoint == results.length
                        console.log('...rule ends at position ' + endpoint)
                        if(lateMatches.length) {
                            console.log('late matches for rule: ' + lateMatches.map(m=>m.resultIndex + ' : ' + trimRecord(m.result)))
                        } else {
                            console.log('no late matches')
                        }
                        rule.endsBy = endpoint

                        // add outcomes for this rule
                        ruleOutcomes.push({'rule':{'label': rule.label, 'priority': ruleIndex, 'endpoint': rule.endsBy}, 'lateMatches': lateMatches})
                    })

                    // all rules run for this case, so add it
                    vm.searchCases.push({'query': {'location':location, 'jobFunction': jobFunction, 'industry': industry}, 
                                        'results': data.results,
                                        'rules': rules,
                                        'outcomes': ruleOutcomes})                    
                })
            }
            d3.json('/static/data/searchTestCases.json').then(data=>{
                data.forEach(c => {
                    checkSearch(c.jobFunction, c.industry, c.location)
                })
            })
        },
        names: function(list) {
            return list.map(e=>e.name ? e.name : e.canonical_name).join(', ')    
        },
        resultShade: function(result) {
            return result.firstRuleMatch == -1 ? 'transparent' : this.shades[result.firstRuleMatch]
        }
    }
})
