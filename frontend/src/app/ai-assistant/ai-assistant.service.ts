/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { Injectable } from '@angular/core'
import { HttpClient } from '@angular/common/http'
import { Observable } from 'rxjs'

@Injectable({ providedIn: 'root' })
export class AiAssistantService {
  private readonly apiUrl = '/api/assistant/ask'

  constructor (private readonly http: HttpClient) {}

  ask (message: string): Observable<{ reply: string }> {
    return this.http.post<{ reply: string }>(this.apiUrl, { message })
  }
}
