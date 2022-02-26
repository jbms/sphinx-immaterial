/*
 * Copyright (c) 2016-2022 Martin Donath <martin.donath@squidfunk.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

import {
  Observable,
  Subject,
  animationFrameScheduler,
  auditTime,
  combineLatest,
  defer,
  distinctUntilChanged,
  finalize,
  map,
  tap,
  withLatestFrom
} from "rxjs"

import {
  Viewport,
  getElement,
  getElementOffset
} from "~/browser"

import { Component } from "../_"
import { Header } from "../header"
import { Main } from "../main"

/* ----------------------------------------------------------------------------
 * Types
 * ------------------------------------------------------------------------- */

/**
 * Sidebar
 */
export interface Sidebar {
  height: number                       /* Sidebar height */
  locked: boolean                      /* Sidebar is locked */
}

/* ----------------------------------------------------------------------------
 * Helper types
 * ------------------------------------------------------------------------- */

/**
 * Watch options
 */
interface WatchOptions {
  viewport$: Observable<Viewport>      /* Viewport observable */
  main$: Observable<Main>              /* Main area observable */
}

/**
 * Mount options
 */
interface MountOptions {
  viewport$: Observable<Viewport>      /* Viewport observable */
  header$: Observable<Header>          /* Header observable */
  main$: Observable<Main>              /* Main area observable */
}

/* ----------------------------------------------------------------------------
 * Functions
 * ------------------------------------------------------------------------- */

/**
 * Watch sidebar
 *
 * This function returns an observable that computes the visual parameters of
 * the sidebar which depends on the vertical viewport offset, as well as the
 * height of the main area. When the page is scrolled beyond the header, the
 * sidebar is locked and fills the remaining space.
 *
 * @param el - Sidebar element
 * @param options - Options
 *
 * @returns Sidebar observable
 */
export function watchSidebar(
  el: HTMLElement, { viewport$, main$ }: WatchOptions
): Observable<Sidebar> {
  const parent = el.parentElement!
  const adjust =
    parent.offsetTop -
    parent.parentElement!.offsetTop

  /* Compute the sidebar's available height and if it should be locked */
  return combineLatest([main$, viewport$])
    .pipe(
      map(([{ offset, height }, { offset: { y } }]) => {
        height = height
          + Math.min(adjust, Math.max(0, y - offset))
          - adjust
        return {
          height,
          locked: y >= offset + adjust
        }
      }),
      distinctUntilChanged((a, b) => (
        a.height === b.height &&
        a.locked === b.locked
      ))
    )
}

/**
 * Mount sidebar
 *
 * This function doesn't set the height of the actual sidebar, but of its first
 * child – the `.md-sidebar__scrollwrap` element in order to mitigiate jittery
 * sidebars when the footer is scrolled into view. At some point we switched
 * from `absolute` / `fixed` positioning to `sticky` positioning, significantly
 * reducing jitter in some browsers (respectively Firefox and Safari) when
 * scrolling from the top. However, top-aligned sticky positioning means that
 * the sidebar snaps to the bottom when the end of the container is reached.
 * This is what leads to the mentioned jitter, as the sidebar's height may be
 * updated too slowly.
 *
 * This behaviour can be mitigiated by setting the height of the sidebar to `0`
 * while preserving the padding, and the height on its first element.
 *
 * @param el - Sidebar element
 * @param options - Options
 *
 * @returns Sidebar component observable
 */
export function mountSidebar(
  el: HTMLElement, { header$, ...options }: MountOptions
): Observable<Component<Sidebar>> {
  const inner = getElement(".md-sidebar__scrollwrap", el)
  const { y } = getElementOffset(inner)
  return defer(() => {
    const push$ = new Subject<Sidebar>()
    push$
      .pipe(
        auditTime(0, animationFrameScheduler),
        withLatestFrom(header$)
      )
        .subscribe({

          /* Handle emission */
          next([{ height }, { height: offset }]) {
            inner.style.height = `${height - 2 * y}px`
            el.style.top       = `${offset}px`
          },

          /* Handle complete */
          complete() {
            inner.style.height = ""
            el.style.top       = ""
          }
        })

    /* Create and return component */
    return watchSidebar(el, options)
      .pipe(
        tap(state => push$.next(state)),
        finalize(() => push$.complete()),
        map(state => ({ ref: el, ...state }))
      )
  })
}
