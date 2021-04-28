var ChannelAnnotationApp = new Vue({
    delimiters: ['[[', ']]'],
    el: '#channel-annotation-app',
    data: {
        channels: [],
        jobFunctions: [],
        industries: [],
        channelTypes: [],
        cursor: 0,
    },
    mounted:  function() {
        d3.json('/annotations/get-channels').then(data=>{
            this.channels = data.channels.sort((a, b)=>a.id - b.id);
            this.cursor = 0
            this.getChannel(this.channels[this.cursor])
        })
        this.type_options = type_options
    },
    methods: {
        getCookie: function(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },
          postType: function(type) {
                let channel = this.channels[this.cursor]
                d3.json('/annotations/set-channel', {
                    method: 'POST',
                    body: JSON.stringify({
                        id: channel.id,
                        type: type,
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8",
                        "X-CSRFToken": this.getCookie('csrftoken')
                    },
                }).then(function(data) {
                    // set back here to confirm done?
                   channel.type = data.type
                }, function(d){
                    console.error(d)
                })
            },
        selectType: function(value) {
            this.postType(value)
            setTimeout(this.next, 400) // time to display change before moving onto next
        },
        next: function() {
            if(this.cursor >= this.channels.length - 1) {
                this.cursor = 0;
            } else {
                 this.cursor++
            }
            this.getChannel(this.channels[this.cursor])
        },
        getChannel: async function(channel) {
            const data = await d3.json('/annotations/get-channel/'+channel.id)
            channel.type = data.type
            this.$set(channel, 'products', data.products)
        },
        cleanURL: function(url) {
            return url ? url.startsWith('http') ? url : 'http://' + url: ''
        }
    },
    watch: {
    },
    computed: {
    }
})
