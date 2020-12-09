var DataQualityApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#data-quality-app',
    data: {
        locations: [],
        products: [],
        jobFunctionTree: {},
        locationTree: {},
        parent_lookup: {},
        branches: {}
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

        d3.json('/annotations/get-boards').then(
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
        }
    },
    computed: {
        checks : function() {
            let canonical_names = this.locations.map(l => l.canonical_name)
            let many_location_threshold = 20
            return [
                {
                    'label': 'Approved Locations with no parent',
                    'values': this.locations.filter(l => l.mapbox_within__canonical_name == null && l.approved)
                        .map(l=>{ return {
                            'label': l.canonical_name,
                            'admin_url': '/admin/products/location/' + l.id + '/change',
                        }
                    })
                },
                {
                    'label': 'Duplicate locations',
                    'values': this.locations
                        .filter((l, index) => canonical_names.lastIndexOf(l.canonical_name) !== index)
                        .map(l=>{ return {
                            'label':l.canonical_name,
                            'admin_url': '/admin/products/location/' + l.id + '/change',
                        }
                    })
                },
                {
                    'label': 'Generic Products with no location tagging',
                    'values': this.products ? this.products
                        .filter(p => p.location.length == 0 && p.location
                            && p.salesforce_product_category == "Generic Product")
                        .map(p=> {
                                return {
                                    'label': p.title,
                                    'admin_url': '/admin/products/product/' + p.id + '/change'
                                }
                            }
                        ) : null
                },
                {
                    'label': 'Products with redundant sub-locations of locations',
                    'values': this.products ? this.productsWithRedundantLocations().map(product => {
                        return {
                            'label': product.title,
                            'admin_url': '/admin/products/product/' + product.id + '/change',
                            'values': product.location.map(l => l.canonical_name)
                        }
                    }) : null
                },
                {
                    'label': `Products with ${many_location_threshold} location taggings or more`,
                    'values': this.products ? this.products.filter(p => p.location.length >= many_location_threshold)
                        .map(p=>{ return {
                            'label':p.title,
                            'admin_url': '/admin/products/product/' + p.id + '/change',
                            'values': [p.location.length]
                        }}) : null
                },
                {
                    'label': `Locations without a continent in context`,
                    'values': this.locations ? this.locations.filter(loc =>
                        typeof loc.mapbox_context == 'object' && !loc.mapbox_context.some(con => con.startsWith('continent.')))
                        .map(loc=>{ return {
                            'label':loc.canonical_name,
                            'admin_url': '/admin/products/product/' + loc.id + '/change',
                            'values': [loc.mapbox_context.join(', ')]
                        }}) : null
                }
            ]
        }
    }
})
