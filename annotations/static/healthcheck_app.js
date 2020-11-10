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

const treeContains = function(tree, name) {
    if(tree.data.name == name) return true
    // let tree = subTreeFromName(name_a)
    if(tree.children) {
        return tree.children.some(child => { return treeContains(child, name) })
    } else return false;
}

function locationFromName(location) { return locs.find(l=>l.name == location)}
function subTreeFromName(name, tree) {
    if( tree.data.name == name) return true
    if( tree.children ) {
        for(child of tree.children) {
            if(subTreeFromName(name, child)) {
                return child
            }
        }
    }
    return false
}


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

let app = new Vue({
            el: '#app',
            delimiters: ['[[', ']]'],
            data() {
                return{
                    // endpoint: "/static/boards.json",

                    endpoint: "/annotations/update-boards",
                    boards: [],
                    checks: {'location': {'redundancy': []}}

                }
            },
            mounted: function(){

                this.fetchBoards();
                // this.fetchJobTitles()
                this.getLocationTree()
                // this.getJobFunctionTree()

                fetch('/static/iso-3166.json')
                        .then(blob => blob.json())
                        .then(data => {
                            // console.log(data)
                            this.ccLookup = d3.nest().key(c=>c['code']).rollup(x=>x[0])
                                .object(data.map(d=>{return {name:d['name'], code:parseInt(d['country-code'])}}))

                        });
            },
            methods: {
                checkLocationRedundancy : function() {
                    let out = []
                    if(this.boards == null) {
                        console.error('No boards to check location of')
                        return
                    }
                    this.boards.forEach(board => {

                        // console.log(board.title)
                        let redundancies = []
                        let r = new Map()
                        board.location.forEach( i => {
                            board.location.forEach( j => {
                                if(i != j && treeContains(subTreeFromName(i, this.locationTree), j)) {
                                    redundancies.push({'parent':i, 'child': j})
                                    if(! r.has(i)) {
                                         r.set(i, new Set([j]))
                                    } else {
                                        r.get(i).add(j)
                                    }
                                }
                            })
                        })
                        if(redundancies.length) {
                            out.push({'board':board, 'redundancies': redundancies, 'r': r})
                        }
                    })
                    this.checks.location.redundancy = out;
                },
                renderLocationRedundancy: function(redundancy) {
                    if(!redundancy) return "spinner"
                    let html = `Tagged locations: <p>${redundancy.board.location.join(', ')}</p>`
                    // redundancy.r.entries().forEach('')
                    // redundancy.r.keys()
                    let list = Array.from(redundancy.r)

                    debug = subTreeFromName(redundancy.board.title, this.locationTree)


                    return html + list.map(i=>`<div>Choose: <b>${i[0]}</b> OR ${Array.from(i[1]).join(', ')}</div>`)
                },

                fetchBoards: function () {
                    fetch(this.endpoint)
                        .then(blob => blob.json())
                        .then(data => {
                            this.boards = []
                            this.boards.push(...data.boards)
                            // this.tallyFacets()
                            // this.tallyLocationTree()

                            d3.selectAll('input').attr('disabled', null)
                            // this.backgroundPrompt = "↖️ Start with a job title..."

                            // fetch("/annotations/update-boards").then(() => { console.log('boards updated') })

                        });
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
            },
             watch: {
                boards: function() {
                    this.checkLocationRedundancy()
                },
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

