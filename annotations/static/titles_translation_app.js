var titleTranslationApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#title-translation-app',
    data: {
        titles: [],
        pageIndex: 0,
        pageSize: 50
    },
    mounted:  function() {
        d3.json('/annotations/get-titles').then(data=> {
            this.titles = data.titles
                .filter(title => title.alias_of__id == null)
                .filter(title => title.active)
                .sort((a, b) => {
                    // return b.frequency - a.frequency
                    return a.name > b.name ? 1 : -1
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
