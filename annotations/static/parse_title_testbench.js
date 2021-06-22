var ParseTitleApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#parse-title-app',
    data: {
        reqs: [],
        testResults: [], // raw title => {'parser_name': list}
        filter: {'algolia':{'match_levels':['full', 'partial']},'bespoke':{'exact_match':true, 'sublist_match': true, 'frequency_match':true}, 'different_function':false},
        limit: 100,
        testSources: [
            {'name':'Problematic Titles', 'key': 'problematic', 'filepath': 'problematic_titles.csv'},
            {'name':'Integrated jobs', 'key':'integrated', 'filepath': 'integrated_jobs_distinct_by_freq.csv'},
            {'name':'Non-Profit Titles', 'key': 'nonprofit', 'filepath': 'nonprofit_titles.csv'}
        ],
        testSource: null,
        interactiveQuery: "",
    },
    mounted: function () {
        this.testSource = this.testSources[0].filepath // triggers load
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
        loadTestData: function() {
            this.testResults = []

            d3.csv('/static/data/'+this.testSource).then(tests => {

                // run parsers of top n
                for(test of tests.slice(0, this.limit)) {
                    this.parseTitle(test.headline, false, test.target_function)
                }
            })
        },
        parseTitle: async function(headline, append= true, target_function) {
            vm = this
            vm.testResults[headline] = {}
            await d3.json('/annotations/parse-title', {
                    method: 'POST',
                    body: JSON.stringify({
                        title: headline
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(d => {
                    // req.updated = true
                    let entry = {'headline': headline, 'parser': 'base_bespoke', 'result': d, 'target_function':target_function}
                    append ? vm.testResults.push(entry) : vm.testResults.unshift(entry)
                })
        },
        renderBespokeResult: function(result) {
            if(result['estimation_type'] == 'exact_match') {
                return `<span class="alert-success">${result['functions'][0]['function']}</span>`
            }

            if(result['estimation_type'] == 'sublist_match') {
                return `<span class="alert-info">${functions.map(f => f['function']).join(', ')}</span>`
            }

            functions = result['functions']

            if(functions.length) {
                return `<ul>${functions
                    .filter(f=>f.weight > 0.05)
                    .map(f=>'<li>'+f['function'] + ' ' + f['weight']?.toFixed(2) + '</li>').join('')}</ul>`
            }
            return ""
        },
        renderAlgoliaResult: function(hits) {
            if(hits.length) {
                return `<ul>${hits.map(h=>'<li><span class="'+h._highlightResult.title.matchLevel+'-match">'+h['func']+'</span><br><small>'
                        +h['_highlightResult']['title']['value']+'</small></li>').join('')}</ul>`
            }
            return ""
        },
        renderAlgoliaHit: function(hit) {
            let titles = hit._highlightResult.all_job_titles
            if(titles.length) {
                return `<h3>${hit.name}</h3><ul>${titles.filter(t=>t['matchLevel'] != 'none').map(t=>'<li class="'+t['matchLevel']+'-match"><small>'
                        +t['value']+'</small></li>').join('')}</ul>`
            }
            return ""
        },
        renderAlgoliaHitLite: function(hit, target_function, rank) {
            let titles = hit._highlightResult.all_job_titles
            if(titles.length) {
                return `<div class="d-inline float-left px-2 mx-1 btn ${target_function?hit.name==target_function?'btn-success':'btn-danger':'btn-secondary'}">
                    ${hit.name}
                    </div>`
            }
            return ""
        },
        bespokeStats: function() {
            let bespokeResults = this.testResults.filter(r=>r.parser == "base_bespoke")
            return {
                'count': bespokeResults.length,
                'exact_match': bespokeResults.filter(r=>r.result.result.estimation_type == "exact_match").length,
                'sublist_match': bespokeResults.filter(r=>r.result.result.estimation_type == "sublist_match").length,
                'frequency_match': bespokeResults.filter(r=>r.result.result.estimation_type == "frequency").length,
            }
        },
        algoliaStats: function() {
            if(! this.testResults) return {'pass':0, 'fail':0, 'unchecked':0, 'n':0}
            return {
                'pass':this.testResults.filter(tr=>tr.result.algolia.hits[0]?.name == tr.target_function).length,
                'fail':this.testResults.filter(tr=>tr.result.algolia.hits[0]?.name !== tr.target_function).length,
                'unchecked':this.testResults.filter(tr=> ! tr.target_function).length,
                'n':this.testResults.length
            }
            // return {
            //     'match_full': this.testResults.filter(r=>r.result.algolia.hits[0]?._highlightResult.title.matchLevel == "full").length,
            //     'match_partial': this.testResults.filter(r=>r.result.algolia.hits[0]?._highlightResult.title.matchLevel == "partial").length,
            //     'match_none': this.testResults.filter(r=>r.result.algolia.hits[0]?._highlightResult.title.matchLevel == "none").length,
            // }
        },
        functionsMatch: function(result) {
            return true
            return this.filter.different_function && result.result.algolia.hits[0]?.func !== result.result.result.functions[0]?.function
        },
        showResult: function(result) {
            // Note: using first result only
            return true;//this.filter.algolia.match_levels.indexOf(result.result.algolia.hits[0]?._highlightResult.title.matchLevel) != -1
        },
        processInteractive: function() {
            console.log('processing...')
            this.parseTitle(this.interactiveQuery, false)
        }
    },
    watch: {
        testSource: function () {
            this.loadTestData()
        },
        limit: function() {
            this.loadTestData()
        }
    }
})
