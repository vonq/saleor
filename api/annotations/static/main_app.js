Vue.component('treeselect', VueTreeselect.Treeselect)

// helper functions
const fix = function(tree) {
  tree.label = tree.data.name
    tree.tally = tree.data.tally
  // delete tree.name
  if(tree.children) {
    tree.children.forEach(fix)
  }
}

const flatten = function(tree) {
  flat = [tree.name]
  if(tree.children) {
    tree.children.forEach(c=>{
      flat = flat.concat(flatten(c))
    })
  }
  return flat
}

const orderChildren = function(tree) {
    tree.children.sort((a,b)=>{
        if(a.children && b.children) {
            // return b.children.length - a.children.length;
            return descendentCount(b) - descendentCount(a)
        }
        if(a.children) return -1;
        if(b.children) return 1;
        return 0
    })
}

const descendentCount = function(tree) {
    if(tree.children) {
        let count = 0
        for(child of tree.children) {
            count += 1 + descendentCount(child)
        }
        return count
    } else return 0;
}

function locationFromName(location) { return locs.find(l=>l.name == location)}
function ancestors(location) {
    if(!location.within__name) return [location];
    else return [location].concat(ancestors(locationFromName(location.within__name)))
}
// ancestors(locationFromName('London'))
function treeCount(locs) {  // for a set of locations for a board
    let counted = [];
    for(loc of locs){
        let ancs = ancestors(locationFromName(loc)); // get ancestors of each locaiton
        for(ancestor of ancs){
            if(!counted.includes(ancestor)){
                counted.push(ancestor)
                if(typeof ancestor.tally == "undefined") ancestor.tally = 1
                else ancestor.tally++
            }
            // else { console.log("already counted " + ancestor.name)}
            // console.log(ancs.map(a=>a.name))
        }
    }
}

Vue.component()

let app = new Vue({
            el: '#app',
            delimiters: ['[[', ']]'],
            data() {
                return{
                    // endpoint: "/static/boards.json",
                    endpoint: "/annotations/update-boards",

                    boards: [],
                    titles: [],
                    locationTree: {},
                    jobFunctionTree: {},
                    trafficRanges : [
                        {'label': 'Any traffic', 'range':[0, Number.MAX_SAFE_INTEGER]},
                        {'label': 'Less than 1000', 'range':[0, 1000]},
                        {'label': '1000 to 10K', 'range':[1000, 10000]},
                        {'label': '10K to 100K', 'range':[10000, 100000]},
                        {'label': '100K to 1M', 'range':[100000, 1000000]},
                        {'label': '1M to 10M', 'range':[1000000, 10000000]},
                        {'label': 'More than 10M', 'range':[10000000, Number.MAX_SAFE_INTEGER]},
                    ],
                    trafficRangeIndex: 0,
                    filterModel: {
                        'text': '',
                        'jobfunctions': [],
                        'industries': [],
                        'location':[],
                        'trafficRange': [],
                        'channel_type': []
                    },
                    filteredBoards: [],
                    facets: [
                        {'field':'jobfunctions', 'name': 'Job function', 'entries':[]},
                        {'field':'channel_type', 'name': 'Channel type', 'entries':[]},
                        {'field':'industries', 'name': 'Industries', 'entries':[]},
                        {'field':'location', 'name': 'Locations', 'entries':[]},
                        ],
                    ccLookup: {},
                    backgroundPrompt: "Loading..."
                }
            },
            mounted: function(){
                new Autocomplete('#autocomplete', {
                  search: input => {
                    const url = `/annotations/autocomplete?q=${encodeURI(input)}`

                    return new Promise(resolve => {
                      if (input.length < 3) {
                        return resolve([])
                      }

                      fetch(url)
                        .then(response => response.json())
                        .then(data => {
                          resolve(data.map(d=>d.name))
                        })
                    })
                  },
                    // renderResult: (result, props) => `
                    //     <li ${props}>
                    //       <div class="wiki-title">
                    //         ${result.name}
                    //       </div>
                    //       <div class="wiki-snippet">
                    //         ${result.jobFunction__name}
                    //       </div>
                    //     </li>
                    //   `,

                  onSubmit: result => {
                      matchedTitle = this.titles.find(t=>t.name==result)
                      if(matchedTitle) {
                          if(matchedTitle.industry__name !== null) {
                              this.filterModel.industries = [matchedTitle.industry__name]
                          }
                          if(matchedTitle.jobFunction__name !== null) {
                            this.filterModel.jobfunctions = [matchedTitle.jobFunction__name]
                          }
                      }
                  }
                })
                d3.selectAll('input').attr('disabled', 'disabled')
                this.fetchBoards();
                this.fetchJobTitles()
                this.getLocationTree()
                this.getJobFunctionTree()

                fetch('/static/iso-3166.json')
                        .then(blob => blob.json())
                        .then(data => {
                            // console.log(data)
                            this.ccLookup = d3.nest().key(c=>c['code']).rollup(x=>x[0])
                                .object(data.map(d=>{return {name:d['name'], code:parseInt(d['country-code'])}}))
                        });
            },
            methods: {
                fetchBoards: function () {
                    fetch(this.endpoint)
                        .then(blob => blob.json())
                        .then(data => {
                            this.boards.push(...data.boards)
                            this.tallyFacets()
                            // this.tallyLocationTree()

                            d3.selectAll('input').attr('disabled', null)
                            this.backgroundPrompt = "↖️ Start with a job title..."
                        });
                },
                fetchJobTitles: function () {
                    fetch('/annotations/titles')
                        .then(blob => blob.json())
                        .then(data => this.titles.push(...data.titles));
                },
                filterBoards: function () {
                    // no matches if no filters
                    if (this.noFilters) {
                        this.filteredBoards = []
                        return;
                    }

                    // helpers
                    const flatten = function (tree) {
                        flat = [tree.label]
                        if (tree.children) {
                            tree.children.forEach(c => {
                                flat = flat.concat(flatten(c))
                            })
                        }
                        return flat
                    }

                    const find = function (tree, val) {
                        if (tree.label == val) return tree;
                        if (!tree.children) return null;
                        let found = null
                        tree.children.forEach(c => {
                            found = found || find(c, val)
                        })
                        return found
                    }

                    let locations = []
                    if (this.filterModel.location.length > 0) {
                        for (loc of this.filterModel.location) {
                            locations = locations.concat(flatten(find(this.locationTree, loc)))
                        }
                    }

                    let functions = []
                    if (this.filterModel.jobfunctions.length > 0) {
                        for (func of this.filterModel.jobfunctions) {
                            functions = functions.concat(flatten(find(this.jobFunctionTree, func)))
                        }
                    }

                    const re = new RegExp(this.filterModel.text, 'gi');
                    this.filteredBoards = this.boards.filter(board => {
                        return board.description.match(re)
                            && (this.filterModel.channel_type == "" || this.filterModel.channel_type.some(type => board.channel_type == type))
                            && (this.filterModel.industries.length == 0 || this.filterModel.industries.some(ind => board.industries.includes(ind)))
                            && (this.filterModel.jobfunctions.length == 0 || functions.some(fun => board.jobfunctions.includes(fun)))
                            && (this.filterModel.location.length == 0 || locations.some(loc => board.location.includes(loc)) || board.location.includes('Global'))
                            && (this.filterModel.trafficRange.length < 2
                                || (this.filterModel.trafficRange[0] < board.total_visits_6_months
                                    && board.total_visits_6_months <= this.filterModel.trafficRange[1]))
                    })
                        .slice(0, 200)
                },

                tallyFacets: function () {
                    for (facet of app.facets) {
                        facet.entries = app.tallyFacet(facet.field)
                            .sort((a, b) =>
                            { return b.value - a.value } // by freq
                            // { return a.key < b.key ? -1 : 1}) // alphabetically
                            )
                    }
                },

                tallyFacet: function (key) {
                    freq = {}
                    if (this.boards.length == 0) return;
                    // need to handle lists as well as scalas
                    this.boards.forEach(board => {
                        if (board[key]) {
                            if (typeof board[key] == 'object') { // assume iterable
                                board[key].forEach(value => {
                                    if (value != null) {
                                        if (value in freq) {
                                            freq[value] = freq[value] + 1;
                                        } else {
                                            freq[value] = 1;
                                        }
                                    }
                                })
                            } else { // single value
                                let value = board[key]
                                if (value != null) {
                                    if (value in freq) {
                                        freq[value] = freq[value] + 1;
                                    } else {
                                        freq[value] = 1;
                                    }
                                }
                            }
                        }
                    })
                    let list = [];
                    for(key in freq){
                        list.push({'key':key, 'value':freq[key]})
                    }
                    return list
                },
                getLocationTree: function () {
                    locs = {};
                    let v = this
                    d3.json('/annotations/locations').then(
                        data => {
                            locs = data.locations
                            // let facet = v.tallyFacet('Locations')

                            locs.forEach(l => {
                                if (l.name !== 'Global' && l.within__name == null) l.within__name = 'Global'
                                // l.tally = Math.random()
                                // l.tally = facet.entries.find(e=>e.key == l.name).value
                            })


                            this.locationTree = d3.stratify()
                                .id(function (d) {
                                    return d.name;
                                })
                                .parentId(function (d) {
                                    return d.within__name;
                                })(locs);

                            fix(this.locationTree)
                            orderChildren(this.locationTree)
                        })

                },

                // Assumes we have location tree AND boards loaded as a precondition!
                tallyLocationTree: function() {
                    if (this.boards.length > 0) {
                        for (board of this.boards) {
                            treeCount(board.location)
                        }
                    } else setTimeout(this.tallyLocationTree, 500)
                },

                getJobFunctionTree: function () {
                    d3.json('/annotations/job-functions').then(
                        data => {
                            funcs = data.jobFunctions
                            funcs.forEach(l => {
                                if (l.parent__name == null) l.parent__name = 'Global'
                            })
                            funcs.push({name:"Global"})
                            this.jobFunctionTree = d3.stratify()
                                .id(function (d) {
                                    return d.name;
                                })
                                .parentId(function (d) {
                                    return d.parent__name;
                                })(funcs);

                            fix(this.jobFunctionTree)
                            orderChildren(this.jobFunctionTree)
                        })
                },
                renderCountryShareTR: function(countryShare) {
                    const roundpc = d3.format(".0p")
                    let name = this.ccLookup[countryShare.country].name
                        .replace("United States of America", "USA")
                        .replace('United Kingdom of Great Britain and Northern Ireland', 'UK')
                    return '<td>'+ name + '</td>'
                        + '<td>' + roundpc(countryShare.value) + '</td><td>' +  roundpc(countryShare.change) + '</td>'
                },
                haveMetaData: function(board) {
                    return board.similarweb_estimated_monthly_visits.length
                        // || board.female_audience_is_predominant
                        || board.similarweb_top_country_shares.length
                        || Object.keys(board.similarweb_estimated_monthly_visits).length
                }
            },
             watch: {
                filterModel: {
                    handler: _.debounce(function() {
                        this.filteredBoards = null
                        this.filterBoards()
                    }, 500),
                    deep: true
                },
                trafficRangeIndex: function() {
                    this.filterModel.trafficRange = this.trafficRanges[this.trafficRangeIndex].range;
                }
            },
            computed : {
                noFilters: function() {
                    return this.filterModel.text == ""
                            && this.filterModel.channel_type == ""
                            && this.filterModel.jobfunctions.length == 0
                            && this.filterModel.industries.length == 0
                            && this.filterModel.location.length == 0
                            && this.filterModel.trafficRange < 2
                },
            }
        });


Vue.component('simple-linechart', {
    props:['data'],
    data: function () {
        entries = []
        for(key in this.data) {
            entries.push({date: new Date(key), freq:this.data[key]})
        }
        // return entries;
        return {
            vals: entries,
            margin: {'y': 10}
        }
    },
    mounted: function () {
        this.initialiseChart()
        this.renderChart()
    },
    computed: {

    },
    watch: {
    },
    methods: {
        initialiseChart: function () {
            let svg = d3.select('#simple-linechart-' + this._uid).style('width', '-webkit-fill-available').style('height', '80px')
            let width = svg.node().clientWidth
            let height = svg.node().clientHeight

            svg.append('rect').attr('x', 0).attr('y', this.margin.y).attr('width', width).attr('height', height - 2 * this.margin.y)
                .attr('fill', '#fff')

            svg.append('path').classed('trend-line')

            // outline mean line
            svg.append('line').attr('x1', 0).attr('x2', width).classed('mean-line', true)
                .style('stroke-width', 3).style('stroke', '#fff').style('stroke-dasharray', 'none')

            svg.append('line').attr('x1', 0).attr('x2', width).classed('mean-line', true)

            svg.append('text').attr('x', width).attr('y', 0).classed('traffic-text', true).classed('max-text', true)
                            .style('font-size', this.margin.y + 'px')
            svg.append('text').attr('x', width).classed('traffic-text', true).classed('min-text', true)
                            .style('font-size', this.margin.y + 'px')

            // outline text
            svg.append('text').attr('x', width/2).classed('traffic-text', true).classed('mean-text', true)
                .style('stroke-width', '2')

            svg.append('text').attr('x', width/2).classed('traffic-text', true).classed('mean-text', true)
        },
        renderChart: function () {
            let svg = d3.select('#simple-linechart-' + this._uid)
            let width = svg.node().clientWidth
            let height = svg.node().clientHeight

            // var data = this.byDay.map(d => {
            //     return {'date': new Date(d[0]), 'freq': d[1].length}
            // })

            var data = this.vals

            // d3.timeDay.range(this.daterange[0], this.daterange[1]).forEach(p => { // fill in
            //     if (!data.some(d => d.date.getTime() == p.getTime())) {
            //         data.push({'date': p, 'freq': 0})
            //         console.log(p)
            //     }
            // })

            data = data.sort((a, b) => a.date.getTime() - b.date.getTime())

            let min = data.reduce((a, c) => {
                return c.freq < a.freq ? c : a
            }).freq

            let max = data.reduce((a, c) => {
                return c.freq > a.freq ? c : a
            }).freq

            svg.select('.max-text').text(max)
            svg.select('.min-text').attr('y', height).text(min)

            let dateScale = d3.scaleTime().domain([data[0].date, data[data.length - 1].date]).range([0, width])
            let yScale = d3.scaleLinear().domain([min, max]).range([height-this.margin.y, this.margin.y])

            let mean = data.map(b=>b.freq).reduce((a, c)=>a + c ) / data.length
            svg.selectAll('.mean-text').attr('y', yScale(mean) - 2).text(Math.round(mean))// + ' / month')
            svg.selectAll('.mean-line').attr('y1', yScale(mean)).attr('y2', yScale(mean))

            svg.select('path').classed('trend-line', true).attr('d',
                d3.line()
                .curve(d3.curveCardinal.tension(0.1))
                .x(d => { return dateScale(d.date)})
                .y(d=>{return yScale(d.freq)})(data))

            svg.select('text').text(max)
        },

    },
    template: `<div class="py-2"><svg :id="'simple-linechart-'+_uid"></svg></div>`
})
