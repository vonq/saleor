var titlesApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#titles-app',
    data: {
        titles: [],
        jobFunctions: [],
        industries: [],
        // channelTypes: [],
        selectedJobFunction: null,
        selectedIndustry: null,
        // selectedChannelType: null,
        filterModel: {'text': '', 'job_function': ''},
        filteredTitles: [],
        titleIndex: 0,
        ignoredTokens: ['consultant', 'manager', 'assistant', 'executive', 'developer'],
        skipDeactivated: true,
        skipAliases: true,
    },
    mounted:  function() {
        d3.json('/annotations/get-titles').then(data=>{
            this.titles = data.titles.sort((a, b) => { return b.frequency - a.frequency})
            d3.selectAll('input').attr('disabled', null)
        })

        // data below loaded inline
        // this.jobFunctions = data.jobFunctions.map(d=>d.name).sort()
        // this.industries = data.industries.map(d=>d.name).sort()
        // this.channelTypes = data.channelTypes.sort()
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
        possibleAliases: function() {
            if(!this.currentTitle) return []
            // tokenise, remove stopwords
            // ideally, sort by words in common
            possibles = [];
            tokens = this.currentTitle.name.toLowerCase().split(' ')
                .filter(t=>this.ignoredTokens.indexOf(t) == -1)
            for (token of tokens) {
                possibles = possibles.concat(this.titles
                    .filter(t=>t.name.toLowerCase().includes(token))
                    .filter(t=>this.currentAliases.indexOf(t) == -1)
                    .filter(t=>t.id !== this.currentTitle.id)
                )
            }
            return Array.from(new Set(possibles)) // de-duping
                .sort((a, b) => {
                    return a.active && !b.active ? -1 : b - a
                }
            )
        },
          postTitleUpdate: function(title) {
                let v = this;

                d3.json('/annotations/update-title', {
                    method: 'POST',
                    body: JSON.stringify(title),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                   // console.log(data)
                    title = data
                }, function(d){
                    console.error(d)
                })
            },
        filterTitles: function() {
                let re = new RegExp(this.filterModel.text, 'gi')
                this.filteredTitles = this.titles.filter(title => {
                    return title.name.match(re)
                })
                    // .sort((a,b)=>a.jobfunctions.length - b.jobfunctions.length)
            },
        next: function() {
            if(this.titles.length) {
                let skip
                do {
                    skip = false
                    this.titleIndex++;
                    if (this.titleIndex >= this.titles.length) this.titleIndex = 0;
                    if(
                        this.titles[this.titleIndex].active == false && this.skipDeactivated ||
                        this.titles[this.titleIndex].alias_of__id !== null && this.skipAliases
                    ) {
                        skip = true
                    }
                } while(skip)
            }
        },
        previous: function() {
            if(this.titles.length) {
                let skip
                do {
                    skip = false
                    this.titleIndex--;
                    if (this.titleIndex < 0) this.titleIndex = this.titles.length - 1;
                    if(
                        this.titles[this.titleIndex].active == false && this.skipDeactivated ||
                        this.titles[this.titleIndex].alias_of__id !== null && this.skipAliases
                    ) {
                        skip = true
                    }
                } while(skip)
            }
        },
        canonify: function(title) {
            // need to ensure that given title is not an alias of any other
            title.canonical = true
            title.alias_of__id = this.currentTitle.id
        },
        decanonify: function(title) {
            // ensure has no aliases to it.
            title.canonical = false
            this.titles.forEach(t => {
                    if(t.alias_of__id == title.id) {
                        t.alias_of__id = null
                        t.alias_of__name = null // don't think we need name...
                    }
                })
        },

        aliasClick: function(alias) {
            if(alias.alias_of__id !== this.currentTitle.id) { // making alias
                alias.alias_of__id = this.currentTitle.id
                // alias.alias_of__name = this.currentTitle.name
                alias.canonical = false
                this.currentTitle.canonical = true
                this.currentTitle.active = true
            } else { // breaking alias
                alias.alias_of__id = null
                // alias.alias_of__name = null
            }
            this.postTitleUpdate(alias)
        },
        currentTitleClick: function() {
            if(this.currentTitle.canonical) {
                this.currentTitle.canonical = false
                // remove any aliases to it
                this.titles.forEach(t => {
                    if(t.alias_of__id == this.currentTitle.id) {
                        t.alias_of__id = null
                        t.alias_of__name = null // don't think we need name...

                        this.postTitleUpdate(t) // TODO handle the indirect reference
                    }
                })
            } else {
                this.currentTitle.canonical = true
            }
        },
        toggleActive: function(title) {
            title.active = !title.active;
            if(!title.active){
                this.decanonify(title) // includes removing aliases of this title
            }
            this.postTitleUpdate(title)
        },
        activate: function(title) {
            title.active = true
            this.postTitleUpdate(title)
        },
         deactivate: function(title) {
            title.active = false
            this.postTitleUpdate(title)
             this.decanonify(title) // includes removing aliases of this title
        },
        goto: function(title) {
            this.titleIndex = this.titles.findIndex(t => t == title)
        },

        gotoId: function(id) {
            this.titleIndex = this.titles.findIndex(t => t.id == id)
        },


        rebase: function(title) { // better names invited - means swapping this title with its canonical form, taking thier aliases
            canonical = this.titles.find(t => t.id == title.alias_of__id)
            if(canonical) { // title is alias of another
                // take other aliases
                this.titles.forEach(t => {
                    if(t.alias_of__id == canonical.id) {
                        t.alias_of__id = title.id
                        this.postTitleUpdate(t)
                    }
                })
                canonical.alias_of__id = title.id
                title.alias_of__id = null

                this.postTitleUpdate(canonical)
                this.postTitleUpdate(title)
                this.titleIndex = this.titles.indexOf(title)
            }
        }
    },
    watch: {
        filterModel: {
            handler: _.debounce(function() {
                this.filterTitles()
            }, 500),
            deep: true
        }
    },
    computed: {
        currentTitle: function(){
            return this.titles[this.titleIndex]
        },
        currentAliases: function() {
            return this.titles.filter(t=>t.alias_of__id == this.currentTitle.id)
        },
        checks: function() {
            return [
                {
                    'titles': this.titles.filter(t => t.canonical && t.alias_of__id !== null),
                    'label': ' canonicals which are also aliases of other titles'
                }
            ]
        },
        counts: function() {
            return [
                // {
                //     'value': this.titles.filter(t => t.canonical).length,
                //     'label': 'canonicals'
                // },
                {
                    'value': this.titles.filter(t => t.alias_of__id != null).length,
                    'label': 'aliases'
                },
                {
                    'value': this.titles.filter(t => t.active).length,
                    'label': 'active'
                }
            ]
        }
    }
})