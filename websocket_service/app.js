const express = require('express')
const app = express()

app.use(require('morgan')('dev'))
app.use(require('helmet')({ contentSecurityPolicy: false }))

app.get('*', (req, res) => {
  res.json({ message: 'Hello there!' })
})

app.use((error, req, res, next) => {
  res.status(error.status || 500)
  res.json({ error: error.message })
})

module.exports = app
