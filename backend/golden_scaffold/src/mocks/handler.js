import { http, HttpResponse } from 'msw'

// Define your API mock handlers here.
// This example mocks a products API endpoint.
export const handlers = [
  http.get('/api/products', () => {
    return HttpResponse.json([
      { id: 1, name: 'Mock Product A' },
      { id: 2, name: 'Mock Product B' },
    ])
  }),
]