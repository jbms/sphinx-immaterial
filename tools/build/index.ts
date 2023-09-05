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

import { spawn } from "child_process"
import * as fs from "fs/promises"
import { minify as minhtml } from "html-minifier"
import * as path from "path"
import rimraf from "rimraf"
import {
  EMPTY,
  Observable,
  concat,
  concatMap,
  debounceTime,
  defer,
  merge,
  mergeMap,
  of,
  scan,
  startWith,
  switchMap,
  toArray,
  zip
} from "rxjs"
import { optimize } from "svgo"

import { base, resolve, watch } from "./_"
import { copyAll } from "./copy"
import {
  transformScript,
  transformStyle
} from "./transform"

/* ----------------------------------------------------------------------------
 * Helper functions
 * ------------------------------------------------------------------------- */

/**
 * Replace file extension
 *
 * @param file - File
 * @param extension - New extension
 *
 * @returns File with new extension
 */
function ext(file: string, extension: string): string {
  return file.replace(path.extname(file), extension)
}

/**
 * Optimize SVG data
 *
 * This function will just pass-through non-SVG data, which makes the pipeline
 * much simpler, as we can reuse it for the license texts.
 *
 * @param data - SVG data
 *
 * @returns Minified SVG data
 */
function minsvg(data: string): string {
  const result = optimize(data, {
    plugins: [
      "preset-default",
      { name: "removeDimensions", active: true },
      { name: "removeViewBox", active: false }
    ]
  })
  return result.data || data
}

/* ----------------------------------------------------------------------------
 * Tasks
 * ------------------------------------------------------------------------- */

const assetLicenses = new Map<string, string>()

/* Copy all assets */
const assets$ = concat(

  /* Copy Material Design icons */
  ...["*.svg", "../LICENSE"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/@mdi/svg/svg",
      to: `${base}/.icons/material`,
      transform: async data => minsvg(data)
    })),

  /* Copy GitHub octicons */
  ...["*.svg", "../../LICENSE"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/@primer/octicons/build/svg",
      to: `${base}/.icons/octicons`,
      transform: async data => minsvg(data)
    })),

  /* Copy FontAwesome icons */
  ...["**/*.svg", "../LICENSE.txt"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/@fortawesome/fontawesome-free/svgs",
      to: `${base}/.icons/fontawesome`,
      transform: async data => minsvg(data)
    })),

  /* Copy Simple icons */
  ...["**/*.svg", "../LICENSE.md"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/simple-icons/icons",
      to: `${base}/.icons/simple`,
      transform: async data => minsvg(data)
    })),

  /* Copy mermaid.js dist */
  ...["mermaid.min.js*", "../LICENSE"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/mermaid/dist",
      to: `${base}/bundles/mermaid`
    })),

  /* Copy mathjax dist */
  ...["tex-mml-chtml.js", "input/tex/extensions/*.js", "output/*.js", "output/**/*.js", "output/chtml/fonts/woff-v2/*.woff", "a11y/*.js", "sre/**/*.json", "../LICENSE"]
    .map(pattern => copyAll(pattern, {
      from: "node_modules/mathjax/es5",
      to: `${base}/bundles/mathjax`
    }))
).pipe(
  concatMap(async x => {
    if (x.match(/LICENSE[^/]*$/)) {
      assetLicenses.set(path.dirname(path.relative("", x)), await fs.readFile(x, {encoding: "utf-8"}))
    }
    return path
  })
)

/* ------------------------------------------------------------------------- */

/* Transform styles */
const stylesheets$ = resolve("**/[!_]*.scss", { cwd: "src/assets" })
  .pipe(
    mergeMap(file => zip(
      of(ext(file, ".css")),
      transformStyle({
        from: `src/assets/${file}`,
        to: ext(`${base}/bundles/${file}`, ".css")
      }))
    )
  )

/* Transform scripts */
const javascripts$ = resolve("**/bundle.ts", { cwd: "src/assets" })
  .pipe(
    mergeMap(file => zip(
      of(ext(file, ".js")),
      transformScript({
        from: `src/assets/${file}`,
        to: ext(`${base}/bundles/${file}`, ".js")
      }))
    )
  )

const bundleLicenses = new Map<string, Map<string, string>>()

/**
 * Writes licenses of all bundled dependencies to sphinx_immaterial/LICENSE
 *
 * @returns Promise that resolves when license file has been written.
 */
async function writeLicenseFile() {
  let licenseText = await fs.readFile("LICENSE", {encoding: "utf-8"})
  for (const [p, license] of assetLicenses) {
    licenseText += `\n\n${  "=".repeat(79)  }\n\n`
    licenseText += `Files: ${p}/\n\n${  license.trim().replaceAll("\r", "")  }\n`
  }
  const bundlePaths = Array.from(bundleLicenses.keys())
  bundlePaths.sort()
  for (const bundlePath of bundlePaths) {
    for (const [dir, license] of bundleLicenses.get(bundlePath)!) {
      licenseText += `\n\n${  "=".repeat(79)  }\n\n`
      licenseText += `File: ${bundlePath}\nFrom: ${dir}\n\n${  license.trim().replaceAll("\r", "")  }\n`
    }
  }
  await fs.writeFile("sphinx_immaterial/LICENSE", licenseText)
}

/* Compute manifest */
const manifest$ = merge(
  ...Object.entries({
    "**/*.scss": stylesheets$,
    "**/*.ts*":  javascripts$
  })
    .map(([pattern, observable$]) => (
      defer(() => process.argv.includes("--watch")
        ? watch(pattern, { cwd: "src" })
        : EMPTY
      )
        .pipe(
          startWith("*"),
          switchMap(() => observable$.pipe(toArray()))
        )
    ))
)
  .pipe(
    scan((prev, mapping) => {
      for (const [sourcePath, {file, licenseMap}] of mapping) {
        bundleLicenses.set(file, licenseMap)
        prev.set(sourcePath, file.replace(`${base}/bundles/`, ""))
      }
      return prev
    }, new Map<string, string>()),
    concatMap(async m => {
      await writeLicenseFile()
      return m
    }),
  )

/* Transform templates */
const templates$ = manifest$
  .pipe(
    switchMap(_manifest => copyAll("**/*.html", {
      from: "src",
      to: base,
      watch: process.argv.includes("--watch"),
      transform: async data => {
        const metadata = require("../../package.json")
        const banner =
          "{#-\n" +
          "  This file was automatically generated - do not edit\n" +
          "-#}\n"

        /* Normalize line feeds and minify HTML */
        const html = data.replace(/\r\n/gm, "\n")
        return banner + minhtml(html, {
          collapseBooleanAttributes: true,
          includeAutoGeneratedTags: false,
          minifyCSS: true,
          minifyJS: true,
          removeComments: true,
          removeScriptTypeAttributes: true,
          removeStyleLinkTypeAttributes: true
        })

          /* Remove empty lines without collapsing everything */
          .replace(/^\s*[\r\n]/gm, "")

          /* Write theme version into template */
          .replace("$md-name$", metadata.name)
          .replace("$md-version$", metadata.version)
      }
    }))
  )

const docs$ = (() => {
  let building = false
  let dirty = false
  return defer(() => process.argv.includes("--watch")
    ? watch(["docs/**", "sphinx_immaterial/**"],
            { ignored: ["**/*.pyc",
              "docs/_build/**",
              "docs/.mypy_cache/**",
              "sphinx_immaterial/.mypy_cache/**",
              "docs/python_apigen_generated/**",
              "docs/cpp_apigen_generated/**"
            ]
            })
        : EMPTY
  ).pipe(startWith("*"),
    debounceTime(100),
    switchMap(async x => {
                if (Array.isArray(x))
                  // eslint-disable-next-line no-console
                  console.log(`building due to change in: ${x[0]}`)
                dirty = true
                if (building) {
                  return
                }
                try {
                  do {
                    building = true
                    dirty = false
                    await new Promise((res, rej) => {
                      rimraf("docs/_build", error => {
                        if (error != null) {
                          rej(error)
                        } else {
                          res(undefined)
                        }
                      })
                    })
                    await new Promise((res, rej) => {
                      rimraf("docs/python_apigen_generated", error => {
                        if (error != null) {
                          rej(error)
                        } else {
                          res(undefined)
                        }
                      })
                    })
                    const child = spawn("sphinx-build", ["docs", "docs/_build", "-a", "-j", "auto"],
                                        {stdio: "inherit"})
                    await new Promise(res => {
                      child.on("exit", res)
                    })
                  } while (dirty)
                } finally {
                  building = false
                }
                return EMPTY
              }))

})()

/* ----------------------------------------------------------------------------
 * Program
 * ------------------------------------------------------------------------- */

/* Assemble pipeline */
const templatesBuild$ =
  process.argv.includes("--dirty")
    ? templates$
    : concat(assets$, templates$)

const build$: Observable<unknown> =
  process.argv.includes("--docs")
    ? merge(templatesBuild$, docs$)
    : templatesBuild$

/* Let's get rolling */
build$.subscribe()
