const express = require('express');
const Unblocker = require('unblocker');

const app = express();
const unblocker = new Unblocker({ prefix: '/proxy/' });

app.use(unblocker);

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
