import { rest } from 'msw';
import fruits from './data/fruits.json';

const handlers = [
  rest.get('https://614c99f03c438c00179faa84.mockapi.io/fruits', (_, response, context) =>
    response(context.json(fruits))
  ),
];

export default handlers;
