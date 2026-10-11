import axios, { type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import api, { AUTH_EXPIRED_EVENT } from './api'
import { clearTokens, getAccessToken, setAccessToken } from '../lib/storage'

function respond(config: InternalAxiosRequestConfig, status: number, data: unknown) {
  const response = { data, status, statusText: String(status), headers: {}, config }
  if (status >= 200 && status < 300) return Promise.resolve(response)
  const err = new axios.AxiosError('fail', String(status), config, null, response as never)
  return Promise.reject(err)
}

describe('api 401 refresh handling', () => {
  const originalAdapter = api.defaults.adapter
  let calls: { url?: string; auth?: string }[]

  beforeEach(() => {
    localStorage.clear()
    setAccessToken('old-access')
    calls = []
  })
  afterEach(() => {
    api.defaults.adapter = originalAdapter
    clearTokens()
    vi.restoreAllMocks()
  })

  it('sends credentials and the CSRF header by default', () => {
    expect(api.defaults.withCredentials).toBe(true)
    expect(api.defaults.headers['X-Requested-With']).toBe('TestPilot')
  })

  it('refreshes via cookie and retries /auth/me once on 401', async () => {
    const post = vi
      .spyOn(axios, 'post')
      .mockResolvedValue({ data: { access_token: 'new-access', token_type: 'bearer' } })
    const adapter: AxiosAdapter = (config) => {
      const auth = String(config.headers.Authorization)
      calls.push({ url: config.url, auth })
      if (auth === 'Bearer new-access') return respond(config, 200, { id: 1 })
      return respond(config, 401, {})
    }
    api.defaults.adapter = adapter

    const res = await api.get('/auth/me')
    expect(res.data).toEqual({ id: 1 })
    expect(post).toHaveBeenCalledTimes(1)
    const [url, body, opts] = post.mock.calls[0]
    expect(String(url)).toMatch(/\/auth\/refresh$/)
    expect(body).toBeUndefined()
    expect(opts).toMatchObject({ withCredentials: true, headers: { 'X-Requested-With': 'TestPilot' } })
    expect(calls).toHaveLength(2)
    expect(getAccessToken()).toBe('new-access')
    expect(localStorage.length).toBe(0)
  })

  it('emits AUTH_EXPIRED_EVENT and clears the token when refresh fails', async () => {
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('401'))
    const onExpired = vi.fn()
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    api.defaults.adapter = (config) => respond(config, 401, {})

    await expect(api.get('/auth/me')).rejects.toBeTruthy()
    window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
    expect(onExpired).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()
  })

  it('does not refresh on /auth/login 401', async () => {
    const post = vi.spyOn(axios, 'post')
    api.defaults.adapter = (config) => respond(config, 401, { detail: 'bad creds' })

    await expect(api.post('/auth/login', {})).rejects.toMatchObject({ response: { status: 401 } })
    expect(post).not.toHaveBeenCalled()
    expect(getAccessToken()).toBe('old-access')
  })
})
