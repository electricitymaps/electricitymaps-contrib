// TODO: validate redirect logic by enabling this:
// process.env.NODE_ENV = 'production';

const { app, server } = require('../server');
const supertest = require('supertest');

const request = supertest(app);

// Stop the server that is started in server.js
server.close();

describe('/health', () => {
  it('responds correctly to a GET request', async () => {
    const response = await request.get('/health');

    expect(response.status).toBe(200);
    expect(response.header['content-type']).toEqual('application/json; charset=utf-8');
    expect(response.body).toEqual({ status: 'ok' });
  });
});

describe('/', () => {
  it('responds correctly to a standard GET request', async () => {
    const response = await request.get('/');

    expect(response.status).toBe(200);
    expect(response.header['content-type']).toEqual('text/html; charset=utf-8');
    expect(response.text).toContain('<!DOCTYPE html>');
    expect(response.text).toContain(
      '<link rel="canonical" href="https://app.electricitymap.org/" />'
    );
  });

  it('adds lang query parameter to canonical link', async () => {
    const response = await request.get('/?lang=en'); // .set('Accept', 'application/json')
    expect(response.text).toContain(
      '<link rel="canonical" href="https://app.electricitymap.org/?lang=en" />'
    );
  });
});
