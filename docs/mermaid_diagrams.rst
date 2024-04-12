.. _Mermaid.js: https://mermaid-js.github.io/mermaid/

Mermaid diagrams
================

.. note::

   This feature provides an alternative to :doc:`graphviz` for including diagrams.

The mkdocs-material theme is equipped to make use of diagrams generated (during page load time)
with `Mermaid.js`_. Although, its implementation relies on a markdown extension that does not get
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

        While all `Mermaid.js`_ features should work out-of-the-box, this theme will currently only
        adjust the fonts and colors for the following types of diagrams:

        .. rst-example:: References linking directly to a diagram's :rst:`:name:`

            - `flowcharts`_
            - `sequence diagrams <sequence-diagrams>`
            - `class diagrams <class-diagrams>`
            - `state diagrams <state-diagrams>`
            - `entity-relationship diagrams <entity-relationship-diagrams>`

Using flowcharts
----------------

`Flowcharts diagrams <https://mermaid.js.org/syntax/flowchart.html>`_ represent
workflows or processes. The steps are rendered as nodes of various kinds and are connected by
edges, describing the necessary order of steps.

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

`Sequence diagrams <https://mermaid.js.org/syntax/sequenceDiagram.html>`_ describe a specific scenario
as sequential interactions between multiple objects or actors, including the messages that are
exchanged between those actors.

.. rst-example::

    .. md-mermaid::
        :name: sequence-diagrams

        sequenceDiagram
          autonumber
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

`State diagrams <https://mermaid.js.org/syntax/stateDiagram.html>`_ are a great tool to describe
the behavior of a system, decomposing it into a finite number of states, and transitions between
those states.

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

`Class diagrams <https://mermaid.js.org/syntax/classDiagram.html>`_ are central to object
oriented programming, describing the structure of a system by modelling entities as classes and
relationships between them.

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

An `entity-relationship diagram <https://mermaid.js.org/syntax/entityRelationshipDiagram.html>`_
is composed of entity types and specifies relationships that exist between entities.
It describes inter-related things in a specific domain of knowledge.

.. rst-example::

    .. md-mermaid::
        :name: entity-relationship-diagrams

        erDiagram
          CUSTOMER ||--o{ ORDER : places
          ORDER ||--|{ LINE-ITEM : contains
          LINE-ITEM {
            string name
            int pricePerUnit
          }
          CUSTOMER }|..|{ DELIVERY-ADDRESS : uses

Other diagram types
-------------------

Besides the diagram types listed above, Mermaid.js provides support for
`pie charts <https://mermaid.js.org/syntax/pie.html>`_,
`gantt charts <https://mermaid.js.org/syntax/gantt.html>`_,
`user journeys <https://mermaid.js.org/syntax/userJourney.html>`_,
`git graphs <https://mermaid.js.org/syntax/gitgraph.html>`_
and `requirement diagrams <https://mermaid.js.org/syntax/requirementDiagram.html>`_,
all of which are not officially supported by sphinx-immaterial.
Those diagrams should still work as advertised by `Mermaid.js`_, but we don't consider them a good
choice, mostly as they don't work well on mobile.
