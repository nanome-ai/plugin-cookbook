const fs = require('fs')
const http = require('http')
const https = require('https')

const app = require('./app')
const ws = require('./ws')
ws.init()

const httpServer = http.createServer(app)
httpServer.on('upgrade', ws.onUpgrade)
httpServer.listen(80)

const options = {
  key: fs.readFileSync('./certs/local.key'),
  cert: fs.readFileSync('./certs/local.crt')
}
const httpsServer = https.createServer(options, app)
httpsServer.on('upgrade', ws.onUpgrade)
httpsServer.listen(443)
