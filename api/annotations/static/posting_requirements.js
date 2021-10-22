LOCATION = "Location"
SALARY_INDICATION = "Salary Indication"
CAREER_LEVEL = "Career Level"
LANGUAGE_SPECIFIC = "Language Specific"
CONTACT_INFO = "Contact Information"
COMPANY_REGISTRATION_INFO = "Company Registration Information"
FB_PROFILE = "Facebook Profile"
LI_PROFILE = "LinkedIn Profile"
XING_PROFILE = "Xing Profile"
HOURS = "Hours"

var PostingRequirementsApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#posting-requirements-app',
    data: {
        reqs: [],
        types: ['location', 'salary', 'career', 'language', 'contact', 'hours'],
        mappings: new Map()
    },
    mounted: function () {
        [
            ['location', LOCATION],
            ['zip', LOCATION],
            ['country', LOCATION],
            ['career', CAREER_LEVEL],
            ['contact_name', CONTACT_INFO],
            ['contact_email', CONTACT_INFO],
            ['contact_zip', CONTACT_INFO],
            ['contact_city', CONTACT_INFO],
            ['contact_company', CONTACT_INFO],
            ['vacancy_language', LANGUAGE_SPECIFIC],
            ['hours', HOURS],

        ].forEach(m => this.mappings.set(m[0], m[1]))

        d3.csv('/static/data/IGB_requirements_for_import.csv').then(
            data => {
                    this.reqs = d3.group(data, d=>d.uuid)
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
        baseQuery: async function(queryString, result) {
            return d3.json(queryString, {
                method: 'GET',
                headers: {
                    "Content-type": "application/json; charset=UTF-8",
                    "X-CSRFToken": this.getCookie('csrftoken')
                },
            })
        },
        processRequirements: async function(requirements) {
            // compose the values for each board
            let mapped
            const mapIt = (value) => {
                if( this.mappings.has(value) ) {
                    mapped.add(this.mappings.get(value))
                }
            }
            for(req of this.reqs){
                mapped = new Set()
                req[1].forEach(r => {
                    // trying both since we don't know how complete they are
                    mapIt(r['Source EN'])
                    mapIt(r['Fallback EN'])
                })

                let requirements = {'uuid': req[0], 'values': Array.from(mapped).join()}
                let v = this;

                console.log('posting ' + requirements.uuid)

                await d3.json('/annotations/set-posting-requirements', {
                    method: 'POST',
                    body: JSON.stringify({
                        uuid: requirements.uuid,
                        values: requirements.values,
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(d => {
                    console.log(d)
                    req.updated = true
                })
            }
        },
        renderReq: function(req) {
            return `<div class="col">${req[0]}</div>
                    <div class="col">${req[1].map(d=>d['Source EN']).join(', ')}</div>
                    <div class="col">${req[1].map(d=>d['Fallback EN']).join(', ')}</div>`
        }
    }
})
