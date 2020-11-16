var titlesApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#titles-app',
    data: {
        titles: [],
        jobFunctions: [],
        industries: [],
        selectedJobFunction: null,
        selectedIndustry: null,
        titleIndex: 0,
        ignoredTokens: ['consultant', 'manager', 'assistant', 'executive', 'developer', 'engineer'],
        skipDeactivated: true,
        skipAliases: true,
        searchIncludesAliases: true
    },
    mounted:  function() {
        d3.json('/annotations/get-titles').then(data=> {
            this.titles = data.titles.sort((a, b) => {
                return b.frequency - a.frequency
            })

            new Autocomplete('#autocomplete', {
                search: input => {
                    return new Promise(resolve => {
                        if (input.length < 3) {
                            return resolve([])
                        }
                        return resolve(this.titles
                            .filter(title => this.searchIncludesAliases || title.alias_of__id == null)
                            .map(title => title.name)
                            .filter(name => name.toLowerCase().includes(input.toLowerCase()))
                            .sort())
                    })
                },
                onSubmit: result => {
                    matchedIndex = this.titles.findIndex(t => t.name == result)
                    if (matchedIndex > -1) {
                        this.titleIndex = matchedIndex
                        $('#autocomplete > input').val('')
                    }
                }
            })
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
        possibleAliases: function() {
            if(!this.currentTitle) return []
            // tokenise, remove stopwords
            possibles = [];
            tokens = this.currentTitle.name.toLowerCase().split(' ')
                .filter(t=>this.ignoredTokens.indexOf(t) == -1)
            for (token of tokens) {
                possibles = possibles.concat(this.titles
                    .filter(title=>title.name.toLowerCase().split(' ')
                        .some(pToken => pToken == token)) // title tokens includes token : count?
                    .filter(t=>this.currentAliases.indexOf(t) == -1)
                    .filter(t=>t.id !== this.currentTitle.id)
                )
            }
            let unique = Array.from(new Set(possibles)) // de-duping
            lexicalMatch = {}
            for (const u of unique) {
                lexicalMatch[u.id] = u.name.toLowerCase().split(' ')
                    .filter(value => tokens.includes(value)).length
            }

            return unique  // sorting by alphabetical, lexical match, active, alias_of, frequency in that order
                .sort((a, b) => {
                    return a.name < b.name ? 1 : -1;
                })
                .sort((a, b) => {
                    return lexicalMatch[a.id] - lexicalMatch[b.id]
                })
                .sort((a, b) => {
                    return a.alias_of__id === null && b.active !== null ? -1 : b - a
                })
                .sort((a, b) => {
                    return a.active && !b.active ? -1 : b - a
                })
        },
        postUpdate: function(title, change) {
                change.id = title.id

                d3.json('/annotations/update-title', {
                    method: 'POST',
                    body: JSON.stringify(change),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                    title.alias_of__id = data.alias_of__id
                    title.canonical = data.canonical
                    title.active = data.active
                }, function(d){
                    alert('Failed to update: ' + title.name)
                })
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
        // canonify: function(title) {
        //     // need to ensure that given title is not an alias of any other
        //     title.canonical = true
        //     title.alias_of__id = this.currentTitle.id
        //
        // },
        decanonify: function(title) {
            // ensure has no aliases to it.
            this.postUpdate(title, {'canonical': false})
            this.titles.forEach(t => {
                if(t.alias_of__id == title.id) {
                    this.postUpdate(t, {'alias_of__id':null, 'alias_of__name':null}) // may not need name...
                }
            })
        },
        aliasClick: function(alias) {
            if(alias.alias_of__id !== this.currentTitle.id) { // making alias
                let secondaryAliases = this.titles.filter(t => t.alias_of__id == alias.id)
                if(secondaryAliases.length == 0 || confirm('This title has ' + secondaryAliases.length + ' aliases.  Continue?')) {
                    this.postUpdate(alias, {
                        'alias_of__id': this.currentTitle.id,
                        'canonical': false,
                        'active': true
                    })
                    for (const sa of secondaryAliases) {
                        this.postUpdate(sa, {
                            'alias_of__id': this.currentTitle.id,
                            'canonical': false,
                            'active': true
                        })
                    }
                    if (!this.currentTitle.active) { // ensure current title active if creating alias to it
                        this.postUpdate(this.currentTitle, {'active': true})
                    }
                    if (!this.currentTitle.canonical) { // may be deprecated
                        this.postUpdate(this.currentTitle, {'canonical': true})
                    }
                }
            } else { // breaking alias
                this.postUpdate(alias, {'alias_of__id': null})
            }
        },
        toggleActive: function(title) {
            if(title.active) this.deactivate(title)
            else if(!title.active) this.activate(title)
        },
        activate: function(title) {
            this.postUpdate(title, {'active': true})
        },
        deactivate: function(title) {
            this.postUpdate(title, {'active': false})
            this.decanonify(title) // includes removing aliases of this title
        },
        goto: function(title) {
            this.titleIndex = this.titles.findIndex(t => t == title)
        },
        gotoId: function(id) {
            this.titleIndex = this.titles.findIndex(t => t.id == id)
        },
        rebase: function(title) { // better names invited - means swapping this title with its canonical form, taking their aliases
            let canonical = this.titles.find(t => t.id == title.alias_of__id)
            if(canonical) { // title is alias of another
                // take other aliases
                this.titles.forEach(t => {
                    if(t.alias_of__id == canonical.id) {
                        this.postUpdate(t, {'alias_of__id': title.id})
                    }
                })
                this.postUpdate(canonical, {'alias_of__id': title.id})
                this.postUpdate(title, {'alias_of__id': null})

                this.titleIndex = this.titles.indexOf(title)
            }
        }
    },
    watch: {
    },
    computed: {
        currentTitle: function(){
            if(this.titles.length) {
                return this.titles[this.titleIndex]
            } else {
                return {'canonical': false, 'active': true, 'name': 'Loading...'}
            }
        },
        currentAliases: function() {
            return this.titles.filter(t=>t.alias_of__id == this.currentTitle.id)
        },
        checks: function() {
            return [
                {
                    'titles': this.titles
                        .filter(t => t.alias_of__id !== null)
                        .filter(a => this.titles.some(t => t.alias_of__id == a.id)),
                    'label': ' alias titles which also have aliases'
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