.. _mermaid.js: https://mermaid-js.github.io/mermaid/

Mermaid diagrams
================

.. note::

   This feature provides an alternative to :doc:`graphviz` for including diagrams.

The mkdocs-material theme is equipped to make use of diagrams generated (during page load time)
with `mermaid.js`_. Although, its implementation relies on a markdown extension that does not get
used by this sphinx-immaterial theme. Thus, the sphinx-immaterial theme provides an optional
directive that exposes the underlying implementation in mkdocs-material theme.

.. rst:directive:: md-mermaid

    .. rst:directive:option:: class
        :type: string

        A space delimited list of qualified names that get used as the HTML element's
        ``class`` attribute.

        .. hint::
            You can use this option to specify ``text-align`` property via the following
            CSS classes:

            - ``align-right`` sets the ``text-align`` property to ``right``.
            - ``align-left`` sets the ``text-align`` property to ``left``.
            - ``align-center`` sets the ``text-align`` property to ``center``.


    .. rst:directive:option:: name
        :type: string

        A qualified name that get used as the HTML element's ``id`` attribute.

        Use the `ref` role to reference the element by name.

    The `md-mermaid` directive's ``:class:`` and ``:name:`` options can be used
    as respective class and id specifiers in custom CSS.

    This theme comes with CSS styling that conforms to the chosen `primary` & `accent` colors
    (based on the selected `scheme`).

    .. failure::

        While all `mermaid.js`_ features should work out-of-the-box, this theme will currently only
        adjust the fonts and colors for the following types of diagrams:

        .. rst-example:: References linking directly to a diagram's ``:name:``

            - `flowcharts`_
            - `sequence diagrams <sequence-diagrams>`
            - `class diagrams <class-diagrams>`
            - `state diagrams <state-diagrams>`
            - `entity-relationship diagrams <entity-relationship-diagrams>`

Using flowcharts
----------------

.. rst-example::

    .. md-mermaid::
        :name: flowcharts

        graph LR
            A[Start] --> B{Error?};
            B -->|Yes| C[Hmm...];
            C --> D[Debug];
            D --> B;
            B ---->|No| E[Yay!];

Using sequence diagrams
-----------------------

.. rst-example::

    .. md-mermaid::
        :name: sequence-diagrams

        sequenceDiagram
            Alice->>John: Hello John, how are you?
            loop Healthcheck
                John->>John: Fight against hypochondria
            end
            Note right of John: Rational thoughts!
            John-->>Alice: Great!
            John->>Bob: How about you?
            Bob-->>John: Jolly good!

Using state diagrams
--------------------

.. rst-example::

    .. md-mermaid::
        :name: state-diagrams

        stateDiagram-v2
            state fork_state <<fork>>
                [*] --> fork_state
                fork_state --> State2
                fork_state --> State3

                state join_state <<join>>
                State2 --> join_state
                State3 --> join_state
                join_state --> State4
                State4 --> [*]


Using class diagrams
--------------------

.. rst-example::

    .. md-mermaid::
        :name: class-diagrams

        classDiagram
            Person <|-- Student
            Person <|-- Professor
            Person : +String name
            Person : +String phoneNumber
            Person : +String emailAddress
            Person: +purchaseParkingPass()
            Address "1" <-- "0..1" Person:lives at
            class Student{
                +int studentNumber
                +int averageMark
                +isEligibleToEnrol()
                +getSeminarsTaken()
            }
            class Professor{
                +int salary
            }
            class Address{
                +String street
                +String city
                +String state
                +int postalCode
                +String country
                -validate()
                +outputAsLabel()
            }

Using entity-relationship diagrams
----------------------------------

.. rst-example::

    .. md-mermaid::
        :name: entity-relationship-diagrams

        erDiagram
            CUSTOMER ||--o{ ORDER : places
            ORDER ||--|{ LINE-ITEM : contains
            CUSTOMER }|..|{ DELIVERY-ADDRESS : uses
