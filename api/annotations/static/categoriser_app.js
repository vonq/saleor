var categoriserApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#categoriser-app',
    data: {
        boards: [],
        jobFunctions: [],
        industries: [],
        channelTypes: [],
        selectedJobFunction: null,
        selectedIndustry: null,
        selectedChannelType: null,
        filterModel: {'text': '', 'job_function': ''},
        filteredBoards: []
    },
    mounted:  function() {
        // d3.json('/static/boards.json').then(data=>{
        d3.json('/annotations/update-boards').then(data=>{
            this.boards = data.boards;
            d3.selectAll('input').attr('disabled', null)
        })

        // data below loaded inline
        this.jobFunctions = data.jobFunctions.map(d=>d.name).sort()
        this.industries = data.industries.map(d=>d.name).sort()
        this.channelTypes = data.channelTypes.sort()
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
          postCategorisation: function(id, field, categoryName) {
                let v = this;

                d3.json('/annotations/add-categorisation', {
                    method: 'POST',
                    body: JSON.stringify({
                        id: id,
                        field: field,
                        categoryName: categoryName
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                   // console.log(data)
                    let board = v.boards.filter(b=>b.id == id)[0]
                    board.industries = data['industry']
                    board.jobfunctions = data['jobFunctions']
                    // set back here
                    board.channel_type = data['channelType']

                }, function(d){
                    console.error(d)
                })
            },
        filterBoards: function() {
                let re = new RegExp(this.filterModel.text, 'gi')
                this.filteredBoards = this.boards.filter(board => {
                    return board.description.match(re)
                }).sort((a,b)=>a.jobfunctions.length - b.jobfunctions.length)
            },
    },
    watch: {
        filterModel: {
            handler: _.debounce(function() {
                this.filterBoards()
            }, 500),
            deep: true
        }
    },
    computed: {
    }
})
