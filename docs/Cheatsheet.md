# WikipediaQL Cheatsheet

## Base syntax

* Select information from one page: `from "Page Name" { selectors }`
* Select information from all pages in a category: `from category:"Category Name" { selectors }`

WikipediaQL query returns data that is fetched by _selectors_. Every terminal selector (one that doesn't have nested ones) adds the text of the matched part of the document to the result set.

* Selectors nesting: `selector1 >> selector 2` -- only `selector2`'s result is added to result set.
* Selector grouping: `{ selector1; selector2 }` -- both `selector1` and `selector2`'s results are added
* Selector naming: `selector as "name` -- adds text fetched by selector to the result set as `"name": selector_value`, constructing the dictionary; unnamed selectors added to the array. The shape of the result set consisting of nested dictionaries and arrays might be quite complicated, WikipediaQL tries to do "the right thing", but the rules of making the result set are work in progress!
* Navigating through pages: `selector_returning_some_links -> { other_selectors }`

## List of selectors

* Any CSS selector works, e.g. `td.red:last-child`;
* `@<any_attribute_name>` selector adds the value of the specified attribute to the result set, for example `a @href as "url"` will add link's URL to the result;
  * besides HTML attributes, `@style-<attr_name>` also work, trying to fetch the value from `style` attribute; it is done because some Wikipedia pages have, say, background-color as a meaningful part of the content (not represented in any other way), so it can be fetched by `@style-background-color`;
  * `@href` and `img@src` attributes are automatically absolutized (so if it is `<a href="/wiki/Some_Page>`, fetching `a @href` would return `https://en.wikipedia.org/wiki/Some_Page`)
* `text` selects the element's full text
* `text:matches("regexp")` selects the part of the element matching the regular expression;
  * `text-group[group_id=1]` or `text-group[group_id="name"]` can be chained to text to fetch parts matched by a regexp;
  * other selectors can be nested, the `text:matches(...)` slices DOM correctly, so it can be `li >> text:matches("^(.+?) as") >> text-group[id=1] >> a@href`
* `sentence:contains("text")` fetches part of the element corresponding to a full sentence containing text. For now, it is the only form of `sentence` working, in future things like `sentence:first`, `sentence:match(...)` etc would be possible.
* `page` selects the whole page; useful for restarting navigation inside the query, or to add page metadata to the result set, like: `page@title`.
* `section[heading="Text"]` selects a section of the Wikipedia page with the heading specified; section heading is not included in the result set; other forms would be possible in the future.
* `table-data` pseudo-selector should be nested directly into `table` and allows nested selector to navigate through restructured table, where it is easier to fetch data. See [Tables.md](./Tables.md) for details and examples.
