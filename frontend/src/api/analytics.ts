import client from './client'

export const login = (email: string, password: string) => {
  const formData = new FormData()
  formData.append('username', email)
  formData.append('password', password)
  return client.post('/api/v1/auth/login', formData)
}

export const getOverview = () =>
  client.get('/api/v1/analytics/overview')

export const getRevenue = () =>
  client.get('/api/v1/analytics/revenue')

export const getPayments = () =>
  client.get('/api/v1/analytics/payments')

export const getCheckout = () =>
  client.get('/api/v1/analytics/checkout')

export const getCustomers = () =>
  client.get('/api/v1/analytics/customers')

export const getSubscriptions = () =>
  client.get('/api/v1/analytics/subscriptions')

export const getRefunds = () =>
  client.get('/api/v1/analytics/refunds')

export const getOpportunities = () =>
  client.get('/api/v1/opportunities/')

export const detectOpportunities = () =>
  client.post('/api/v1/opportunities/detect/')

export const getStrategy = (question: string) =>
  client.post('/api/v1/agent/strategy', { question })
