Vue.component('treeselect', VueTreeselect.Treeselect)

var ProductAnnotationApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#product-annotation-app',
    data: {
        boards: [],
        jobFunctions: [],
        industries: [],
        channelTypes: [],
        selectedJobFunction: null,
        selectedIndustry: null,
        selectedChannelType: null,
        filterModel: {'text': '', 'job_function': ''},
        filteredBoards: [],
        annotationMode: 'iterate', // 'filter' or 'iterate'
        boardIndex: 0, // for when we want to iterate through boards
        industryMapping: null,
        industryToAdd: '',
        jobFunctionTree: {},
        migrationIndustryName: ''
    },
    mounted:  function() {
        d3.json('/annotations/get-products-text').then(data=>{
            data.products_text.forEach(product => {
                product.location = []
                product.industries = []
                product.jobfunctions = []
            })
            this.boards = data.products_text.sort((a, b)=>a.id - b.id);
            d3.selectAll('input').attr('disabled', null)
        })

        d3.json('/static/industry_mapping.json').then(data=>{
            this.industryMapping = data
        })

        // data below loaded inline ensure they are ready
        this.jobFunctions = data.jobFunctions.map(d=>d.name).sort()
        this.industries = data.industries.map(d=>d.name).sort()
        this.channelTypes = data.channelTypes.sort()

        // set up trees
        this.getJobFunctionTree()
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
                    // set back here to confirm done
                    let board = v.boards.filter(b=>b.id == id)[0]
                    board.industries = data['industry']
                    board.jobfunctions = data['jobFunctions']
                    board.channel_type = data['channelType']

                }, function(d){
                    console.error(d)
                })
            },
        filterBoards: function() {
                let re = new RegExp(this.filterModel.text, 'gi')
                this.filteredBoards = this.boards.filter(board => {
                    return board.description_en !== null && board.description_en.match(re)
                })//.sort((a,b)=>a.jobfunctions.length - b.jobfunctions.length)
            },
        next: function() {
            if(this.boards.length == 0) return;

            this.boardIndex = parseInt(this.boardIndex) + 1
            if(this.boardIndex == this.boards.length) this.boardIndex = 0
        },
        prev: function() {
            if(this.boards.length == 0) return;

            this.boardIndex = parseInt(this.boardIndex) - 1
            if(this.boardIndex == -1) this.boardIndex = this.boards.length - 1

        },
        addIndustry: function(industryName) {
            this.postCategorisation(this.focusBoard.id, 'industries', industryName)
            this.industryToAdd = ''
        },
        suggestedIndustries: function() {
            if(this.focusBoard.salesforce_industries) {
                return this.focusBoard.salesforce_industries
                    .map(industry => this.industryMapping[industry])
                    .filter(industry => industry !== null)
                    .flat()
                    .filter(industry => !this.focusBoard.industries.includes(industry))
            } else return []
        },
         getJobFunctionTree: function () {
            // helper functions
            const fix = function(tree) {
                tree.label = tree.data.name
                tree.tally = tree.data.tally
              // delete tree.name
              if(tree.children) {
                tree.children.forEach(fix)
              }
            }

            d3.json('/annotations/job-functions').then(
                data => {
                    funcs = data.jobFunctions
                    funcs.forEach(l => {
                        if (l.parent__name == null) l.parent__name = 'All'
                    })
                    funcs.push({name:"All"})
                    this.jobFunctionTree = d3.stratify()
                        .id(function (d) {
                            return d.name;
                        })
                        .parentId(function (d) {
                            return d.parent__name;
                        })(funcs);
                    fix(this.jobFunctionTree)
                    this.jobFunctionTree.children.sort((a, b)=>{return a.label > b.label ? 1 : -1})
                })
        },
         setCategories: function(field) { // for multiple values
                let board = this.focusBoard // in case it changes during request

                d3.json('/annotations/set-category-values', {
                    method: 'POST',
                    body: JSON.stringify({
                        id: board.id,
                        field: field,
                        categoryNames: board.jobfunctions
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                    // should set back here to confirm done
                }, function(d){
                    console.error(d)
                })
        },
        migrateIndustryToCategory: function() {
            let vm = this
            d3.json('/annotations/migrate-industry-to-category', {
                    method: 'POST',
                    body: JSON.stringify({
                        industry_name: vm.migrationIndustryName,
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                    // should set back here to confirm done
                }, function(d){
                    console.error(d)
                })
        }
    },
    watch: {
        filterModel: {
            handler: _.debounce(function() {
                this.filterBoards()
            }, 500),
            deep: true
        },

        focusBoard: function() {
            console.log('focus board changed')
        }
    },
    computed: {
        focusBoard: function() {
            let board = this.boards[this.boardIndex]
            d3.json('/annotations/get-product/' + board.id).then(data=>{
                board.location = data.product.location
                board.industries = data.product.industries
                board.salesforce_industries = data.product.salesforce_industries
                board.jobfunctions = data.product.jobfunctions
            })
            return board
        },
    }
})
