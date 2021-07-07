var DataQualityApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#data-quality-app',
    data: {
        locations: [],
        products: null,
        jobFunctions: [],
        industries: [],
        locationTree: {},
        parent_lookup: {},
        branches: {},
        filters: [],
        showPassingChecks: true,
        checkLevels: {
            'danger':{
                'selector': 'level-danger',
                'ordering': 0,
            },
            'warning':{
                'selector': 'level-warning',
                'ordering': 1
            },
            'info':{
                'selector': 'level-info',
                'ordering': 2
            }
        },
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

        d3.json('/annotations/get-products').then(
            data => {
                this.products = data.boards
            }
        )
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
        setLocations: function(id, locations) {
            let v = this;

            d3.json('/annotations/set-locations', {
                method: 'POST',
                body: JSON.stringify({
                    id: id,
                    locations: locations,
                }),
                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": this.getCookie('csrftoken')
                },
            }).then(function(data) {
                // can set back here to confirm done
            }, function(d){
                console.error(d)
            })
        },
        productsWithRedundantLocations : function() {
            if(this.products.length == 0) return []

            return this.products.filter(product => {
                let prod_loc_ids = product.location.map(l=>l.mapbox_id)
                return product.salesforce_product_category == 'Generic Product'
                    && product.location.some(loc =>
                        this.branches[loc.mapbox_id].some(anc => prod_loc_ids.includes(anc))
                    )
            })
        },
        pruneRedundantProductLocations : function(product) {
            let prod_loc_ids = product.location.map(l=>l.mapbox_id)
            let cleanedLocations = product.location.filter(loc =>
                // !prod_loc_ids.includes(this.parent_lookup[loc.mapbox_id])

                !this.branches[loc.mapbox_id].some(anc => prod_loc_ids.includes(anc))
            )
            this.setLocations(product.id, cleanedLocations.map(l=>l.canonical_name))
        },
        pruneAllRedundantProductLocations : function() {
            for(product of this.productsWithRedundantLocations()){
                this.pruneRedundantProductLocations(product)
            }
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
        classesFor: function(check) {
            let obj = {}
            obj[this.checkLevels[check.level].selector] = true
            return obj
        },
        checkOrder: function(check){
            return this.checkLevels[check.level].ordering
        },
        freqDist: function(array, field) {
            let fd = {}
            for(e of array) {
                fd[e[field]] = fd[e[field]] ? fd[e[field]] + 1 : 1
            }
            return fd
        },
    },
    computed: {
        checks : function() {
            let canonical_names = this.locations.map(l => l.canonical_name)
            let many_location_threshold = 25

            return [
                    {
                        'label': 'Approved Locations with no parent Location',
                        'type': 'simple',
                        'level': 'warning',
                        'pass': this.locations.filter(l => l.mapbox_within__canonical_name == null && l.approved).length == 0,
                        'values': this.locations.filter(l => l.mapbox_within__canonical_name == null && l.approved)
                            .map(l=>{ return {
                                'label': l.canonical_name,
                                'admin_url': '/admin/products/location/' + l.id + '/change/',
                            }
                            })
                    },
                    {
                        'label': 'Duplicate location names',
                        'type': 'simple',
                        'level': 'warning',
                        'pass': false,
                        'values': this.locations
                            .filter((l, index) => canonical_names.lastIndexOf(l.canonical_name) !== index)
                            .map(l=>{ return {
                                'label': l.canonical_name,
                                'admin_url': '/admin/products/location/' + l.id + '/change/',
                            }})
                            .sort((a,b) => {
                                return a.canonical_name < b.canonical_name ? -1: 1
                            })
                    },
                    {
                        'label': 'Products with redundant sub-locations of locations',
                        'type': 'structured',
                        'level': 'info',
                        'pass': this.products ? this.productsWithRedundantLocations().length == 0: true,
                        'values': this.products ? this.productsWithRedundantLocations().map(product => {
                            return {
                                'label': product.title,
                                'admin_url': '/admin/products/product/' + product.id + '/change/',
                                'values': product.location.map(l => l.canonical_name)
                            }
                        }) : null
                    },
                    {
                        'label': `Products with ${many_location_threshold} location taggings or more`,
                        'type': 'structured',
                        'level': 'info',
                        'pass': this.products ? !this.products.some(p => p.location.length >= many_location_threshold) : true,
                        'values': this.products ? this.products.filter(p => p.location.length >= many_location_threshold)
                            .map(p=>{ return {
                                'label':p.title,
                                'admin_url': '/admin/products/product/' + p.id + '/change/',
                                'values': [p.location.length]
                            }}) : null
                    },
                    {
                        'label': `Locations without a continent in context`,
                        'type': 'structured',
                        'level': 'warning',
                        'pass': true,
                        'values': this.locations ? this.locations.filter(loc =>
                            typeof loc.mapbox_context == 'object' && !loc.mapbox_context.some(con => con.startsWith('continent.')))
                            .map(loc=>{ return {
                                'label':loc.canonical_name,
                                'admin_url': '/admin/products/location/' + loc.id + '/change/',
                                'values': [loc.mapbox_context.join(', ')]
                            }}).sort((a,b) => {
                                return a.canonical_name < b.canonical_name ? -1: 1
                            }) : null
                    },
                    {
                        'label': `Active Boards with no location tagging, including 'International'`,
                        'type': 'simple',
                        'level': 'warning',
                        'pass': this.products ? !this.products.some(p => p.location.length == 0 && p.location
                                && p.salesforce_product_category == "Generic Product" && p.is_active==true) : true,
                        'values': this.products ? this.products
                            .filter(p => p.location.length == 0 && p.location
                                && p.salesforce_product_category == "Generic Product" && p.is_active==true)
                            .map(p=> {
                                    return {
                                        'label': p.title,
                                        'admin_url': '/admin/products/product/' + p.id + '/change/'
                                    }
                                }
                            ) : null
                    },
                    {
                        'label': `Boards that look like add-ons or services`,
                        'type': 'simple',
                        'level': 'warning',
                        'pass': false,
                        'values': this.products ? this.products
                            .filter(p => {
                                let campaign_re = new RegExp('Campaign');

                                return p.salesforce_product_category == "Generic Product"
                                && p.title !== null
                                && (
                                    p.title.toLowerCase().startsWith('extra customer success') ||
                                    p.title.toLowerCase().indexOf('add on') != -1 ||
                                    p.title.toLowerCase().indexOf('costs') != -1 ||
                                    p.title.toLowerCase().indexOf('campaign') != -1 ||
                                    p.title.toLowerCase().indexOf('set up') != -1 ||
                                    p.title.startsWith('Wallet ') ||
                                    campaign_re.test(p.title.toLowerCase())
                                )
                            })


                            .map(p=> {
                                    return {
                                        'label': p.title,
                                        'admin_url': '/admin/products/product/' + p.id + '/change/'
                                    }
                                }
                            ) : null
                    },
                    {
                        'label': `Active Products with 'Disabled' or 'Blacklisted' status`,
                        'type': 'simple',
                        'level': 'danger',
                        'pass': false,
                        'values': this.products ? this.products
                            .filter(p => {
                                return true //p.salesforce_product_category == "Generic Product"
                                && p.is_active
                                && ( p.status == 'Disabled' || p.status == 'Blacklisted')
                            })
                            .map(p=> {
                                    return {
                                        'label': p.title,
                                        'admin_url': '/admin/products/product/' + p.id + '/change/'
                                    }
                                }
                            ) : null
                    },
                    {
                            'label': 'Locations without a mapbox_id',
                            'type': 'simple',
                            'level': 'danger',
                            'pass': this.locations ? this.locations.filter(l=>l.mapbox_id==null).length == 0 : true,
                            'values': this.locations ? this.locations.filter(l=>l.mapbox_id==null)
                                .map(l=> {
                                        return {
                                            'label': l.canonical_name,
                                            'admin_url': '/admin/products/location/' + l.id + '/change/'
                                        }
                                    }
                                ) : null
                    },
                    {
                            'label': 'Boards without a logo',
                            'type': 'simple',
                            'level': 'warning',
                            'pass': this.products ? !this.products.some(p=>p.salesforce_product_category == "Generic Product"
                                    && p.logo_url==null) : true,
                            'values': this.products ? this.products.filter(p=>p.salesforce_product_category == "Generic Product"
                                    && p.logo_url==null)
                                .map(p=> {
                                        return {
                                            'label': p.title,
                                            'admin_url': '/admin/products/product/' + p.id + '/change/'
                                        }
                                    }
                                ) : null
                    }
                ]
                .sort((a,b)=>this.checkLevels[a.level].ordering - this.checkLevels[b.level].ordering)
            },
        checksPassingCount : function () {
            return this.checks.filter(check => check.pass).length
        },
        productStats : function() {
            if (this.products === null) {
                return {}
            }
            return {
                'status': {
                    'disabled': this.products.filter(p => p.status == 'Disabled').length,
                    'blacklisted': this.products.filter(p => p.status == 'Blacklisted').length,
                    'active': this.products.filter(p => p.status === null).length
                }
            }
        }
    }
})
