(use-modules (guix build-system pyproject)
             (guix git)
             (guix packages)
             (guix licenses)
             (gnu packages))

(include "manifest.scm")

(package
  (name "python-radiant-net-scraper")
  (version "0.0.0")
  (source (local-file
            (dirname (current-filename))
                     #:recursive? #t
                     #:select? (lambda
                                 (file stat)
                                 ; Exclude hidden dirs & files.
                                 (not (string=?
                                        (string-copy (basename file) 0 1)
                                        ".")))))
  (build-system pyproject-build-system)
  (propagated-inputs %packages)
  (native-inputs %dev-packages)
  (home-page "https://github.com/Cormochamelion/radiantNetScraper/")
  (synopsis "Scraping & saving usage data from radiantNet or similar websites.")
  (description "")
  (license expat))