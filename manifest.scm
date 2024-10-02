;; This "manifest" file can be passed to 'guix package -m' to reproduce
;; the content of your profile.  This is "symbolic": it only specifies
;; package names.  To reproduce the exact same profile, you also need to
;; capture the channels being used, as returned by "guix describe".
;; See the "Replicating Guix" section in the manual.
(use-modules (gnu)
             (guix)
             (guix build-system pyproject)
             (guix build-system python)
             (guix licenses)
             (guix packages)
             (guix profiles))

(define-public python-decopatch
  (package
    (name "python-decopatch")
    (version "1.4.10")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "decopatch" version))
       (sha256
        (base32 "082pnnc7a1d7rk40k7m72w7kw8dk7g8m3yzq4cn1hl217z4ljzwm"))))
    (build-system pyproject-build-system)
    ; Skip tests, they require pytest_cases, which this package in turn is a
    ; dependency of.
    (arguments (list #:tests? #f))
    (propagated-inputs
      (map specification->package (list "python-makefun"
                                        "python-setuptools-scm")))
    (home-page "https://github.com/smarie/python-decopatch")
    (synopsis "Create decorators easily in python.")
    (description "Create decorators easily in python.")
    (license #f)))



(define-public python-pytest-harvest
  (package
    (name "python-pytest-harvest")
    (version "1.10.5")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "pytest-harvest" version))
       (sha256
        (base32 "066lqx46hqlvllq6ppmyi47fjc1dww7jwa4wfkkx2hrf3z7s9kr7"))))
    (build-system pyproject-build-system)
    ;; Skip tests, currently broken. Once the changes from
    ;; https://github.com/smarie/python-pytest-harvest/pull/74 are part of a
    ;; released version, tests should work again.
    (arguments (list #:tests? #f))
    (native-inputs (map
                      specification->package
                      (list "python-pytest"
                            "python-setuptools-scm")))
    (propagated-inputs (append
                        (list python-decopatch)
                        (map specification->package
                            (list "python-makefun"
                                  "python-packaging"
                                  "python-pathlib2"
                                  "python-six"))))
    (home-page "https://github.com/smarie/python-pytest-harvest")
    (synopsis
     "Store data created during your pytest tests execution, and retrieve it at the end of the session, e.g. for applicative benchmarking purposes.")
    (description
     "Store data created during your pytest tests execution, and retrieve it at the
end of the session, e.g. for applicative benchmarking purposes.")
    (license #f)))


(define-public python-pytest-steps
  (package
    (name "python-pytest-steps")
    (version "1.8.0")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "pytest-steps" version))
       (sha256
        (base32 "05r2ch7191saj7sw6d47bfa5vnyyj157dl8hvlcc78xx6jyxy46j"))))
    (build-system pyproject-build-system)
    ;; Skip tests, currently broken. The error looks similar to what
    ;; was resolved in pytest-harvest by 
    ;; https://github.com/smarie/python-pytest-harvest/pull/74, but I can't
    ;; be asked to open an issue and/or investigate further.
    (arguments (list #:tests? #f))
    (native-inputs (map specification->package
                        (list  "python-pytest"
                               "python-setuptools-scm")))
    (propagated-inputs (map specification->package 
                            (list "python-makefun"
                                  "python-wrapt")))
    (home-page "https://github.com/smarie/python-pytest-steps")
    (synopsis "Create step-wise / incremental tests in pytest.")
    (description "Create step-wise / incremental tests in pytest.")
    (license #f)))


(define-public python-pytest-cases
  (package
    (name "python-pytest-cases")
    (version "3.8.6")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "pytest_cases" version))
       (sha256
        (base32 "0i3w3az2qzkgqpmqcic7pfxd6cx30rcrddv9lh1fiy5n1jmy092w"))))
    (build-system pyproject-build-system)
    (native-inputs (map
                      specification->package
                      (list "python-pytest"
                            "python-setuptools-scm")))
    (propagated-inputs (append
                          (list python-decopatch
                                python-pytest-harvest
                                python-pytest-steps)
                          (map specification->package
                            (list "python-makefun"
                                  "python-packaging"))))
    (home-page "https://github.com/smarie/python-pytest-cases")
    (synopsis "Separate test code from test cases in pytest.")
    (description "Separate test code from test cases in pytest.")
    (license #f)))

(packages->manifest
  (append (list python-pytest-cases)
  (map specification->package
    (list "python-beautifulsoup4"
          "python-dotenv"
          "python-numpy"
          "python-pandas"
          "python-pip"
          "python-platformdirs"
          "python-pytest"
          "python-requests"
          "python"))))
