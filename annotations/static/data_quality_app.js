var DataQualityApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#data-quality-app',
    data: {
        locations: [],
        products: [],
        jobFunctionTree: {},
        locationTree: {}
    },
    mounted: function () {
        d3.json('/annotations/locations').then(
            data => {
                this.products = data.products
            }
        )

        d3.json('/annotations/locations').then(
            data => {
                this.locations = data.locations
            }
        )

        d3.json('/annotations/update-boards').then(
            data => {
                this.products = data.boards
            }
        )
    },
    computed: {
        checks : function() {
            let canonical_names = this.locations.map(l => l.canonical_name)
            let many_location_threshold = 20
            return [
                {
                    'label': 'Locations with no parent',
                    'values': this.locations.filter(l => l.mapbox_within__canonical_name == null)
                        .map(l=>l.canonical_name)
                },
                {
                    'label': 'Duplicate locations',  // child + parent
                    'values': this.locations
                        .filter((l, index) => canonical_names.lastIndexOf(l.canonical_name) !== index)
                        .map(l => l.canonical_name)
                },
                {
                    'label': 'Products with no location tagging',
                    'values': this.products ? this.products.filter(p => p.location.length == 0)
                        .map(p=>[p.title, p.id]) : null
                },
                {
                    'label': `Products with ${many_location_threshold} location taggings or more`,
                    'values': this.products ? this.products.filter(p => p.location.length >= many_location_threshold)
                        .map(p=>[p.title, p.id]) : null
                }
            ]
        }
    }
})
