.. _mermaid.js: https://mermaid-js.github.io/mermaid/

Mermaid diagrams
================

.. note::
    Use of this feature has no affect or affiliation with sphinx's graphviz implementation.

The mkdocs-material theme is equipped to make use of diagrams generated (during page load time)
with `mermaid.js`_. Although, its implementation relies on a markdown extension that does not get
used by this sphinx-immaterial theme. Thus, the sphinx-immaterial theme provides with an optional
directive that exposes the underlying implementation in mkdocs-material theme.

.. confval:: md-mermaid

    The `md-mermaid` directive does support the ``:class:`` and ``:name:`` options which can used
    as respective class and id specifiers in custom CSS.

    This theme comes with CSS styling that conforms to the chosen primary & accent colors
    (based on the selected scheme).

    .. md-admonition::
        :class: missing
    
        While all `mermaid.js`_ features should work out-of-the-box, This theme will currently only
        adjust the fonts and colors for `flowcharts`_, `sequence diagrams <sequence-diagrams>`,
        `class diagrams <class-diagrams>`, `state diagrams <state-diagrams>`, and
        `entity-relationship diagrams <entity-relationship-diagrams>`.

Using flowcharts
----------------

.. code-block:: rst

    .. md-mermaid::
        :name: flowcharts

        graph LR
            A[Start] --> B{Error?};
            B -->|Yes| C[Hmm...];
            C --> D[Debug];
            D --> B;
            B ---->|No| E[Yay!];

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

.. code-block:: rst

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

.. code-block:: rst

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


.. code-block:: rst

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


.. code-block:: rst

    .. md-mermaid::
        :name: entity-relationship-diagrams

        erDiagram
            CUSTOMER ||--o{ ORDER : places
            ORDER ||--|{ LINE-ITEM : contains
            CUSTOMER }|..|{ DELIVERY-ADDRESS : uses

.. md-mermaid::
    :name: entity-relationship-diagrams

    erDiagram
        CUSTOMER ||--o{ ORDER : places
        ORDER ||--|{ LINE-ITEM : contains
        CUSTOMER }|..|{ DELIVERY-ADDRESS : uses
