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
  bufferCount,
  combineLatestWith,
  debounceTime,
  defer,
  distinctUntilChanged,
  distinctUntilKeyChanged,
  finalize,
  map,
  of,
  repeat,
  scan,
  share,
  skip,
  startWith,
  switchMap,
  takeLast,
  takeUntil,
  tap,
  withLatestFrom
} from "rxjs"

import { feature } from "~/_"
import {
  Viewport,
  getElement,
  getElements,
  getLocation,
  getOptionalElement,
  watchElementSize
} from "~/browser"

import {
  Component,
  getComponentElement
} from "../_"
import { Header } from "../header"

/* ----------------------------------------------------------------------------
 * Types
 * ------------------------------------------------------------------------- */

/**
 * Table of contents
 */
export interface TableOfContents {
  prev: HTMLAnchorElement[][]          /* Anchors (previous) */
  next: HTMLAnchorElement[][]          /* Anchors (next) */
}

/* ----------------------------------------------------------------------------
 * Helper types
 * ------------------------------------------------------------------------- */

/**
 * Watch options
 */
interface WatchOptions {
  viewport$: Observable<Viewport>      /* Viewport observable */
  header$: Observable<Header>          /* Header observable */
  excludedLinks?: Set<HTMLElement>     /* sphinx-immaterial: Links to exclude */
}

/**
 * Mount options
 */
interface MountOptions {
  viewport$: Observable<Viewport>      /* Viewport observable */
  header$: Observable<Header>          /* Header observable */
  target$: Observable<HTMLElement>     /* Location target observable */
  localToc: boolean
}

/* ----------------------------------------------------------------------------
 * Functions
 * ------------------------------------------------------------------------- */

/**
 * Watch table of contents
 *
 * This is effectively a scroll spy implementation which will account for the
 * fixed header and automatically re-calculate anchor offsets when the viewport
 * is resized. The returned observable will only emit if the table of contents
 * needs to be repainted.
 *
 * This implementation tracks an anchor element's entire path starting from its
 * level up to the top-most anchor element, e.g. `[h3, h2, h1]`. Although the
 * Material theme currently doesn't make use of this information, it enables
 * the styling of the entire hierarchy through customization.
 *
 * Note that the current anchor is the last item of the `prev` anchor list.
 *
 * @param el - Table of contents element
 * @param options - Options
 *
 * @returns Table of contents observable
 */
export function watchTableOfContents(
  el: HTMLElement, { viewport$, header$, excludedLinks }: WatchOptions
): Observable<TableOfContents> {
  const table = new Map<HTMLAnchorElement, HTMLElement>()

  /* Compute anchor-to-target mapping */
  const anchors = getElements<HTMLAnchorElement>("a[href]", el)
  for (const anchor of anchors) {
    if (excludedLinks?.has(anchor)) continue
    const href = anchor.getAttribute("href")!
    let target: HTMLElement|undefined
    if (href.startsWith("#")) {
      const id = decodeURIComponent(anchor.hash.substring(1))
      target = getOptionalElement(`[id="${id}"]`)
    } else {
      target = getOptionalElement(`a.pseudo-toc-entry[href=${CSS.escape(href)}]`)
    }
    if (typeof target !== "undefined") {
      const link = anchor.closest(".md-nav__link")
      if (link !== null) {
        table.set(link as HTMLAnchorElement, target)
      }
    }
  }

  /* Compute necessary adjustment for header */
  const adjust$ = header$
    .pipe(
      distinctUntilKeyChanged("height"),
      map(({ height }) => {
        const main = getComponentElement("main")
        const grid = getElement(":scope > :first-child", main)
        return height + 0.8 * (
          grid.offsetTop -
          main.offsetTop
        )
      }),
      share()
    )

  /* Compute partition of previous and next anchors */
  const partition$ = watchElementSize(document.body)
    .pipe(
      distinctUntilKeyChanged("height"),

      /* Build index to map anchor paths to vertical offsets */
      switchMap(body => defer(() => {
        let path: HTMLAnchorElement[] = []
        return of([...table].reduce((index, [anchor, target]) => {
          while (path.length) {
            const last = table.get(path[path.length - 1])!
            if (last.tagName >= target.tagName) {
              path.pop()
            } else {
              break
            }
          }

          /* If the current anchor is hidden, continue with its parent */
          let offset = target.offsetTop
          while (!offset && target.parentElement) {
            target = target.parentElement
            offset = target.offsetTop
          }

          /* Map reversed anchor path to vertical offset */
          return index.set(
            [...path = [...path, anchor]].reverse(),
            offset
          )
        }, new Map<HTMLAnchorElement[], number>()))
      })
        .pipe(

          /* Sort index by vertical offset (see https://bit.ly/30z6QSO) */
          map(index => new Map([...index].sort(([, a], [, b]) => a - b))),
          combineLatestWith(adjust$),

          /* Re-compute partition when viewport offset changes */
          switchMap(([index, adjust]) => viewport$
            .pipe(
              scan(([prev, next], { offset: { y }, size }) => {
                const last = y + size.height >= Math.floor(body.height)

                /* Look forward */
                while (next.length) {
                  const [, offset] = next[0]
                  if (offset - adjust < y || last) {
                    prev = [...prev, next.shift()!]
                  } else {
                    break
                  }
                }

                /* Look backward */
                while (prev.length) {
                  const [, offset] = prev[prev.length - 1]
                  if (offset - adjust >= y && !last) {
                    next = [prev.pop()!, ...next]
                  } else {
                    break
                  }
                }

                /* Return partition */
                return [prev, next]
              }, [[], [...index]]),
              distinctUntilChanged((a, b) => (
                a[0] === b[0] &&
                a[1] === b[1]
              ))
            )
          )
        )
      )
    )

  /* Compute and return anchor list migrations */
  return partition$
    .pipe(
      map(([prev, next]) => ({
        prev: prev.map(([path]) => path),
        next: next.map(([path]) => path)
      })),

      /* Extract anchor list migrations */
      startWith({ prev: [], next: [] }),
      bufferCount(2, 1),
      map(([a, b]) => {

        /* Moving down */
        if (a.prev.length < b.prev.length) {
          return {
            prev: b.prev.slice(Math.max(0, a.prev.length - 1), b.prev.length),
            next: []
          }

        /* Moving up */
        } else {
          return {
            prev: b.prev.slice(-1),
            next: b.next.slice(0, b.next.length - a.next.length)
          }
        }
      })
    )
}

/* ------------------------------------------------------------------------- */

/**
 * Mount table of contents
 *
 * @param el - Table of contents element
 * @param options - Options
 *
 * @returns Table of contents component observable
 */
export function mountTableOfContents(
  el: HTMLElement, { viewport$, header$, target$, localToc }: MountOptions
): Observable<Component<TableOfContents>> {
  return defer(() => {
    const push$ = new Subject<TableOfContents>()

    /* sphinx-immaterial: use separate active class for local vs global toc */
    const activeClassName = localToc ? "md-nav__link--active" : "md-nav__link--in-viewport"
    push$.subscribe(({ prev, next }) => {
      /* Look forward */
      for (const [anchor] of next) {
        anchor.classList.remove("md-nav__link--passed")
        anchor.classList.remove(
          activeClassName
        )
      }

      /* Look backward */
      for (const [index, [anchor]] of prev.entries()) {
        anchor.classList.add("md-nav__link--passed")
        anchor.classList.toggle(
          activeClassName,
          index === prev.length - 1
        )
      }
    })

    /* sphinx-immaterial: auto-scroll toc */
    if (feature("toc.follow") && (localToc || !feature("toc.integrate"))) {
      let scrollToCurrentPageLinkByDefault = !localToc || feature("toc.integrate")
      push$.pipe(debounceTime(1)).subscribe(({prev}) => {
        let curLink: HTMLElement|undefined
        if (prev.length === 0 && scrollToCurrentPageLinkByDefault) {
          curLink = (el.querySelector("a[href='#']") ?? el) as HTMLElement| undefined
        }
        scrollToCurrentPageLinkByDefault = false
        if (prev.length !== 0) {
          curLink = prev[prev.length - 1][0]
        }
        if (curLink === undefined) return
        if (!curLink.offsetHeight) return
        // Find closest scrollable ancestor.
        let scrollParent = curLink.parentElement
        // On Firefox 101, the `scrollHeight` is sometimes 1 pixel
        // larger than the `clientHeight` on non-scrollable elements.
        const scrollHeightEpsilon = 5
        while (scrollParent !== null &&
               scrollParent.scrollHeight - scrollHeightEpsilon <= scrollParent.clientHeight) {
          scrollParent = scrollParent.parentElement
        }
        if (scrollParent !== null && scrollParent !== document.body &&
            scrollParent !== document.documentElement) {
          const linkRect = curLink.getBoundingClientRect()
          const scrollRect = scrollParent.getBoundingClientRect()
          scrollParent.scrollTo({
            top: scrollParent.scrollTop + (linkRect.y - scrollRect.height / 2 - scrollRect.y)})
        }
      })
    }

    /* Set up anchor tracking, if enabled */
    if (localToc && feature("navigation.tracking"))
      viewport$
        .pipe(
          takeUntil(push$.pipe(takeLast(1))),
          distinctUntilKeyChanged("offset"),
          debounceTime(250),
          skip(1),
          takeUntil(target$.pipe(skip(1))),
          repeat({ delay: 250 }),
          withLatestFrom(push$)
        )
          .subscribe(([, { prev }]) => {
            const url = getLocation()

            /* Set hash fragment to active anchor */
            const anchor = prev[prev.length - 1]
            if (anchor && anchor.length) {
              const [active] = anchor
              const { hash } = new URL(active.href)
              if (url.hash !== hash) {
                url.hash = hash
                history.replaceState({}, "", `${url}`)
              }

            /* Reset anchor when at the top */
            } else {
              url.hash = ""
              history.replaceState({}, "", `${url}`)
            }
          })

    /* sphinx-immaterial: sticky toc headings */
    if (feature("toc.sticky")) {
      watchElementSize(document.body).pipe(distinctUntilKeyChanged("width"),
        debounceTime(0)).subscribe(() =>  {
          // The `position: sticky` CSS feature by itself is
          // sufficient to enable a single level of "sticky" headings.
          // To display multiple levels of sticky headings, it is
          // necessary to specify a `top` position for each nested
          // heading that is exactly the sum of the heights of the
          // ancestor headings.  For fixed-height headings that can be
          // done statically, but this theme wraps long titles.
          // Therefore, we must use JavaScript to compute the
          // necessary top positions for each heading.
          const existingHeights = new Map<HTMLElement, {height: string, zindex: number}>()
          const heightProperty = "--md-nav__header-height"
          for (const link of getElements(".md-nav__link", el)) {
            const nav = link.nextElementSibling
            if (!(nav instanceof HTMLElement) || nav.tagName !== "NAV") {
              continue
            }
            let heightStr = ""
            let zindex = NaN
            const parentNav = nav.parentElement!.closest("nav")
            if (parentNav !== null) {
              const info = existingHeights.get(parentNav)
              if (info !== undefined) {
                heightStr = `${info.height} + `
                zindex = info.zindex - 1
              }
            }
            if (isNaN(zindex)) {
              zindex = 100
            }
            heightStr += `${link.offsetHeight}px + 0.625em`
            link.classList.add("md-nav__sticky")
            link.style.setProperty("--md-nav__sticky-zindex", zindex.toString())
            nav.style.setProperty(heightProperty, `calc(${heightStr})`)
            existingHeights.set(nav, {height: heightStr, zindex})
          }
        })
    }

    const excludedLinks = localToc
      ? undefined
      : new Set(getElements<HTMLElement>("[data-md-component='toc'] a[href]", el))

    /* Create and return component */
    return watchTableOfContents(el, { viewport$, header$, excludedLinks })
      .pipe(
        tap(state => push$.next(state)),
        finalize(() => push$.complete()),
        map(state => ({ ref: el, ...state }))
      )
  })
}
