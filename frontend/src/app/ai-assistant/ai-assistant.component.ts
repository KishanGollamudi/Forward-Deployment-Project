/*
 * Copyright (c) 2014-2026 Bjoern Kimminich & the OWASP Juice Shop contributors.
 * SPDX-License-Identifier: MIT
 */

import { Component, ElementRef, ViewChild } from '@angular/core'
import { CommonModule } from '@angular/common'
import { FormsModule } from '@angular/forms'
import { MatIconModule } from '@angular/material/icon'
import { MatButtonModule } from '@angular/material/button'
import { MatInputModule } from '@angular/material/input'
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'
import { AiAssistantService } from './ai-assistant.service'

interface Message {
  role: 'user' | 'assistant'
  text: string
}

@Component({
  selector: 'app-ai-assistant',
  templateUrl: './ai-assistant.component.html',
  styleUrls: ['./ai-assistant.component.scss'],
  imports: [CommonModule, FormsModule, MatIconModule, MatButtonModule, MatInputModule, MatProgressSpinnerModule]
})
export class AiAssistantComponent {
  @ViewChild('messageList') messageList!: ElementRef

  isOpen = false
  input = ''
  loading = false
  messages: Message[] = [
    { role: 'assistant', text: 'Hi! Ask me anything about our products or pricing.' }
  ]

  constructor (private readonly aiService: AiAssistantService) {}

  toggle (): void {
    this.isOpen = !this.isOpen
  }

  send (): void {
    const text = this.input.trim()
    if (!text || this.loading) return

    this.messages.push({ role: 'user', text })
    this.input = ''
    this.loading = true

    this.aiService.ask(text).subscribe({
      next: (res) => {
        this.messages.push({ role: 'assistant', text: res.reply })
        this.loading = false
        this.scrollToBottom()
      },
      error: () => {
        this.messages.push({ role: 'assistant', text: 'Sorry, I could not reach the assistant right now.' })
        this.loading = false
        this.scrollToBottom()
      }
    })

    this.scrollToBottom()
  }

  onKeydown (event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      this.send()
    }
  }

  private scrollToBottom (): void {
    setTimeout(() => {
      if (this.messageList) {
        this.messageList.nativeElement.scrollTop = this.messageList.nativeElement.scrollHeight
      }
    }, 50)
  }
}
