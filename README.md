# YASS
Yet Another Static Site generator

As bare-bones as a static site generator can be, taking less than 50% of the time as something like Jekyll.
YASS structures your entire site as a tree, where every page is either a table of contents of its children,
or an end page. The defaults are meant to work nicely with GitHub Pages, but could be used in a number
of scenarios where you just want to serve a directory tree as a website. 

All templating is done via [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/).

## Overall structure

```
├── data  # see data_dir below
│   ├── page1
│   ├── page2
│   ├── sublevel1
│   │   ├── page1.1
│   │   └── page1.2
│   ├── sublevel2
│   │   ├── page2.1
│   │   ├── sublevel2.1
│   │   │   └── page2.1.1
│   │   └── page2.2
│   .
│   .
├── docs  # see site_dir below
│   ├── CNAME
│   └── static
├── sitemap.json  # see sitemap_file below
├── templates  # see templates_dir below
│   ├── template_blog.html
│   ├── template_gallery.html
│   .
│   .
```

## `sitemap` structure
The structure of the sitemap json essentially reflects the structure of the `data_dir`, and tells YASS how to interpret the data files and how to arrange the children of a page.
Each element in the json either gives information about how to get rendered (if it's an end page), or has a list of its children (if not). The structure of the sitemap is identical
at every level - the config options available at each level are:

* `children`:  
Optional (the presence of this defines whether it will an end page or a contents page).  
Specify the children of the page (if any) as a list of sitemaps.
* `data_type`:  
Optional. Only for end pages. One of `json`, `markdown`, `text`. Defaults to `text`.  
Makes the data in the corresponding file available as the variable `data` within your templates.  
    * `text`: `data` will be the entire text blob as-is
    * `json`: `data` will be a dict of those values
    * `markdown`: `data` will be the `marko`-produced conversion of the given Markdown to HTML
* `route`:  
Required at all levels.  
Defines the web route for the level, as well as the name of the data file/directory within `data_dir` that will be looked up if this is an end page. For the top level, this should be the empty string `""`.
* `template`:  
Required at all levels.  
Defines the Jinja template to be used at each of these levels, which will be looked up in `templates_dir`. This allows you to define your own contents page template, and in fact allows you to define several contents page templates where you could use a different one in each place. If it is a contents page, a parameter called `contents` will be made available in your template, containing a list of maps of `{"title": <title>, "link": <link>}` of the child pages that can then be displayed however you wish.
* `title`:  
Required at all levels.  
Defines how the parent of this page will refer to this page, and also is made available in your template directly as `title` that can be used however you wish.
    * `tab_title`:  
Optional. Defaults to `title`.  
An additional, admittedly odd parameter - makes the `tab_title` variable available in your templates, in cases where you might want the actual page title to be different that the `title`. Only matters if you actually use it in your templates, and the generator does not control any behavior with it.

### Example
```json
{
  "title": "YASS - Yet Another Static Site Generator",
  "tab_title": "YASS",
  "template": "template_index.html",
  "route": "",
  "children": [
    {
      "title": "Documentation",
      "route": "documentation",
      "template": "template_contents.html",
      "children": [
        {
          "title": "Installation",
          "route": "installation",
          "template": "template_documentation.html",
          "data_type": "text"
        },
        {
          "title": "Usage",
          "route": "usage",
          "template": "template_documentation.html",
          "data_type": "text"
        },
      ]
    },
    {
      "title": "Testimonials",
      "route": "testimonials",
      "template": "template_testimonials.html",
      "data_type": "json"
    }
  ]
}
```

### Variables available in your templates
The above section went over some of this, but to summarize:
* `contents`: present if this is not an end-page, a list of maps of `{"title": <title>, "link": <link>}` of the child pages
* `data`: the actual data of the page, either a json or text blob based on the sitemap definition
* `title`: this is what the parent of a page will be given as part of its children list
* `tab_title`: additional parameter that defaults to `title` that you can use as the actual HTML title if you wish
* `parent_page`: a link to the parent page
* `static_url`: defaults to the empty string, but can be used to switch out the source of your statics
* All parameters in `global_template_parameters` (see below)

## Configuration
All configurations are optional, and have default values:
* `data_dir`:  
The location of the raw data of your site, structured in a tree. Each data file should either be raw text or json; if it is json, it will be used as parameters to the template.  
Example: `./data`
* `global_template_parameters`:  
Dictionary of parameters that should be provided to every single page. Could be used for generating sites for different environments, or to create your own opinionated template set that you then use to generate multiple similar sites.
* `permanent_paths`:  
List of files with the generated site path that should never be cleared out, since the hosting service you use might require certain files in the directory that's being hosted; you may also have static files that shouldn't be impacted.  
Example: `["CNAME", "static"]`
* `site_dir`:  
The directory that your site will be served out of, and where all the generated files will be populated.  
Example: `./docs`
* `sitemap_file`:  
Path to your sitemap file, as defined above.  
Example: `./sitemap.json`
* `static_url`:  
URL for all your static assets. If your templates use the form `{{ static_url }}/path/to/static`, then the generator will make sure to populate it correctly. This way, you can generate sites for multiple environments that use statics in different locations - even localhost.  
Example: `https://assets.example.com`, or `/static/assets` for local use
* `templates_dir`:  
Directory with all the templates mentioned in your sitemap.  
Example: `./templates`
* `template_functions_file`:  
Path to a file containing any custom functions you'd like to use in your templates. Each function you want available must begin with `yass_`; this prefix will be stripped out while injecting it. So, `yass_foo` will be available in your templates as `foo`.  
Example: `yass_template_functions.py`

## GitHub Action usage

YASS comes with a GitHub action that can generate the statics for you (either for testing or deployment)

See [action.yml](https://github.com/purajit/YASS/blob/main/action.yml)

### Example

```yaml
jobs:
  deploy_site:
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Generate statics
        uses: purajit/YASS@v2.0
        with:
          yass-config-path: yass_config_prod.json

      # Futher deploy steps
```

## Notes
### Automatic sitemap generation from `data_dir`
I considered a structure where the files in `data_dir` automatically tell the generator how to deal with them and how to arrange them - essentially as a way to completed remove the `sitemap` json, since that does essentially copy the structure over.

However, I prefer the sitemap being explicit and all in one place; this also allows you to have "staging" data in your `data_dir` that doesn't get hosted until you want it to be. It also makes the code and readability much, much simpler.

## Future work
* Allow for templating of static files

## Used by
<p align="center">
<a href="https://purajit.com">Site</a> | <a href="https://github.com/purajit/purajit.github.io">GitHub</a>
</p>
<p align="center">
<img alt="purajit.com" src="https://github.com/purajit/YASS/blob/main/assets/purajitcom.png?raw=true"  width="45%">
</p>
<p align="center">
<a href="https://mythmancer.com">Site</a> | <a href="https://github.com/mythmancer/mythmancer.github.io">GitHub</a>
</p>
<p align="center">
<img alt="mythmancer.com" src="https://github.com/purajit/YASS/blob/main/assets/mythmancer.png?raw=true"  width="45%">
</p>
