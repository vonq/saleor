var titleTranslationApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#title-translation-app',
    data: {
        titles: [],
        pageIndex: 0,
        pageSize: 50,
        orderedTitles: []
    },
    mounted:  function() {
        d3.json('/annotations/get-titles').then(data=> {
            this.titles = data.titles
                .filter(title => title.alias_of__id == null)
                .filter(title => title.active)
                .sort((a, b) => {
                    if(this.titleSeen(a) && this.titleSeen(b)) return b.frequency - a.frequency
                    if(!this.titleSeen(a) && this.titleSeen(b)) return 1
                    if(this.titleSeen(a) && !this.titleSeen(b)) return -1
                    return b.frequency - a.frequency
                    // return a.name > b.name ? 1 : -1
                })
        })

        d3.csv('/static/ordered_job_titles.csv').then(data => {
            this.orderedTitles = data.map(d=>d.title
                .toLowerCase()
                .replace('(m/w/d)', '')
                .replace('(w/m/d)', '')
                .replace('(m/w/x)', '')
                .replace('(d/f/m)', '')
                .trim()
            )
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
        postUpdate: function(title) {
                d3.json('/annotations/update-title', {
                    method: 'POST',
                    body: JSON.stringify(title),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                    title.active = data.active,
                    title.name_de = data.name_de,
                    title.name_nl = data.name_nl
                }, function(d){
                    alert('Failed to save: ' + title.name)
                })
            },
        nextPage: function() {
            this.pageIndex = parseInt(this.pageIndex) + 1
            if(this.pageIndex * this.pageSize > this.titles.length) {
                alert('No more titles - thanks!')
                return;
            }
        },
        fillIn: function(title) {
            let empty = function(x){ return x == null || x.trim().length == 0 }
            if(empty(title.name_de)) title.name_de = title.name_en
            if(empty(title.name_nl)) title.name_nl = title.name_en
            this.postUpdate(title)
        },
        titleSeen: function(title) {
            return this.orderedTitles.includes(title.name_en.toLowerCase())
                || (title.name_nl && this.orderedTitles.includes(title.name_nl.toLowerCase()))
                || (title.name_de && this.orderedTitles.includes(title.name_de.toLowerCase()))
        },
        seenCount: function() {
            return this.titles.filter(t=>this.titleSeen(t)).length
        },
        setFromTranslators: function() {
             d3.csv('/static/data/merged_job_title_translations.csv').then(async data => {
                 for(loaded_title of data) {
                     let prior_title = this.titles.find(t=>t.name_en == loaded_title.name_en)
                     prior_title.name_nl = loaded_title['Dutch Translator']
                     prior_title.name_de = loaded_title['German Translator']
                     await d3.json('/annotations/update-title', {
                        method: 'POST',
                        body: JSON.stringify(prior_title),
                        headers: {
                            "Content-type": "application/json; charset=UTF-8",
                            "X-CSRFToken": this.getCookie('csrftoken')
                        },
                    }).then(function(data) {
                        prior_title.active = data.active,
                        prior_title.name_de = data.name_de,
                        prior_title.name_nl = data.name_nl
                    }, function(d){
                        alert('Failed to save: ' + prior_title.name)
                    })
                 }
             })
        }
    },
    watch: {
        pageIndex: function() {
            this.pageIndex = parseInt(this.pageIndex) // control manipulation results in a string otherwise
        }
    },
    computed: {
    }
})
