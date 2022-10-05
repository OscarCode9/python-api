let chai = require('chai');
let chaiHttp = require('chai-http');
const expect = require('chai').expect;
chai.use(chaiHttp);
const url = 'http://127.0.0.1:5000';
const assert = require('chai').assert


describe('users controllers ', () => {

  it('should insert a user', (done) => {
    chai.request(url)
      .post('/user')
      .send({ password: 'OscarMartinez', name: "Croacia", admin: true })
      .end(function (err, res) {
        console.log(res.body)
        expect(res).to.have.status(200);
        done();
      });
  });

  it('should get all users', (done) => {
    chai.request(url)
      .get('/api/v1/users')
      .set('x-access-token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdWJsaWNfaWQiOiJlODM3ZjZlMi02YzQ1LTRkNmMtYTc0NC02YWVhMGU0YzUzZDYiLCJleHAiOjE1MzU1MTc5ODR9.rQkiztj8xsJ-AbqHrXcJkUNb3nZxCgPNKU3CWDX8qCc')
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        console.log(res.body)
        users = res.body.users;
        expect(res).to.have.status(200);
        done();    // <= Test completes before this runs
      });
  })


  let users = []

  callbackDelete = function (user) {
    chai.request(url)
      .delete('/user/' + user.public_id)
      .end(function (err, res) {
        console.log(res.body)
        expect(res).to.have.status(200);
        done();
      });
  }
/*
  it('should get all users', (done) => {
    chai.request(url)
      .get('/users')
      .set('x-access-token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdWJsaWNfaWQiOiJlODM3ZjZlMi02YzQ1LTRkNmMtYTc0NC02YWVhMGU0YzUzZDYiLCJleHAiOjE1MzU1MTc5ODR9.rQkiztj8xsJ-AbqHrXcJkUNb3nZxCgPNKU3CWDX8qCc')
      .set("Content-Type", "application/json")
      .end(function (err, res) {
        console.log(res.body)
        users = res.body.users;

        for (let index = 0; index < users.length; index++) {
          const user = users[index];
          it('should delete this ' + user.public_id, callbackDelete(user))
        }

        expect(res).to.have.status(200);
        done();    // <= Test completes before this runs
      });
  })*/
})





