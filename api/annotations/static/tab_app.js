
let app = new Vue({
            el: '#app',
            delimiters: ['[[', ']]'],
            data() {
                return {
                    locationInput: "",
                    mapbox_json_response: "",
                    places: [],
                    used_types: ['place', 'locality', 'country', 'region']
                }
            },
            mounted: function() {
                new Autocomplete('#autocomplete', {
                    search: input => {
                        // const url = `/recommender/autocomplete?q=${encodeURI(input)}`
                        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${this.locationInput}.json?access_token=pk.eyJ1Ijoic2hlbGxzaSIsImEiOiJja2ZwYXp6cXYwNzhqMnRwYm1qbDY2ZDhhIn0.YpFcOs9L53AoHgXWrvvuug&cachebuster=2601464500789&autocomplete=true`

                        return new Promise(resolve => {
                            if (input.length < 3) {
                                return resolve([])
                            }

                            fetch(url)
                                .then(response => response.json())
                                .then(data => {
                                    let places = data.features
                                        .filter(f=>f.place_type.some(t=>this.used_types.includes(t)))
                                    resolve(places)
                                })
                        })
                    },

                    getResultValue: result => result.text,

                    renderResult: (result, props) => `
                    <li ${props}>
                      <div class="input-text">
                        ${result.text}
                      </div>
                      <div class="input-placename">
                        ${result.place_name}
                      </div>
                    </li>
                  `,


                    // onSubmit: result => {
                    //     matchedTitle = this.titles.find(t => t.name == result)
                    //     if (matchedTitle) {
                    //         if (matchedTitle.industry__name !== null) {
                    //             this.filterModel.industries = [matchedTitle.industry__name]
                    //         }
                    //         if (matchedTitle.jobFunction__name !== null) {
                    //             this.filterModel.jobfunctions = [matchedTitle.jobFunction__name]
                    //         }
                    //     }
                    // }
                })
            },
            watch : {
                locationInput: function() {
                    if(this.locationInput.length < 4) return;

                    d3.json(`https://api.mapbox.com/geocoding/v5/mapbox.places/${this.locationInput}.json?access_token=pk.eyJ1Ijoic2hlbGxzaSIsImEiOiJja2ZwYXp6cXYwNzhqMnRwYm1qbDY2ZDhhIn0.YpFcOs9L53AoHgXWrvvuug&cachebuster=2601464500789&autocomplete=true`)
                        .then(data => {
                            this.mapbox_json_response = data;

                            this.places = app.mapbox_json_response.features
                                .filter(f=>f.place_type.some(t=>this.used_types.includes(t)))

                        })
                }
            }
})
