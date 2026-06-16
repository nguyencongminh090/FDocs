import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => {
  const instance = vi.fn().mockResolvedValue({ data: 'retry-ok' })
  instance.interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
  return { default: { create: vi.fn(() => instance) } }
})

import { initApiInterceptors } from './api'
import axios from 'axios'

// api.js calls axios.create() at module load — grab the registered error handler
const mockInstance = axios.create.mock.results[0].value
const [, onRejected] = mockInstance.interceptors.response.use.mock.calls[0]

function make401(withAuth = false) {
  return {
    response: { status: 401 },
    config: {
      _retried: undefined,
      headers: withAuth ? { Authorization: 'Bearer old-token' } : {},
    },
  }
}

describe('api interceptor — refresh token loop prevention', () => {
  let refreshMock

  beforeEach(() => {
    refreshMock = vi.fn().mockResolvedValue('new-token')
  })

  it('does NOT call refresh when login returns 401 (no Authorization header)', async () => {
    initApiInterceptors({ getToken: () => null, refresh: refreshMock })
    await expect(onRejected(make401(false))).rejects.toMatchObject({ response: { status: 401 } })
    expect(refreshMock).not.toHaveBeenCalled()
  })

  it('does NOT call refresh when refresh endpoint returns 401 (no Authorization header)', async () => {
    initApiInterceptors({ getToken: () => null, refresh: refreshMock })
    const error = { response: { status: 401 }, config: { headers: {} } }
    await expect(onRejected(error)).rejects.toMatchObject({ response: { status: 401 } })
    expect(refreshMock).not.toHaveBeenCalled()
  })

  it('calls refresh exactly once when an authenticated request gets 401', async () => {
    initApiInterceptors({ getToken: () => 'old-token', refresh: refreshMock })
    await onRejected(make401(true))
    expect(refreshMock).toHaveBeenCalledTimes(1)
  })

  it('does NOT retry a request that already has _retried=true', async () => {
    initApiInterceptors({ getToken: () => 'old-token', refresh: refreshMock })
    const error = make401(true)
    error.config._retried = true
    await expect(onRejected(error)).rejects.toMatchObject({ response: { status: 401 } })
    expect(refreshMock).not.toHaveBeenCalled()
  })
})
