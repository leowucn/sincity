|    Selector    |                                         Description                                          |                                      Example                                       |
|----------------|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
|  ::first-line  |                        Matches the first textual line in an element.                         |     p::first-line { font-weight: bold } matches the first line in a paragraph      |
| ::first-letter |                           Matches the first letter in an element.                            |     p::first-letter { font-size: 2em } matches the first letter in a paragraph     |
|    ::before    | Used with the content property to generate content before the initial content of an element. | h1::before { content: "*" } places an asterisk at the start of a top-level heading |
|    ::after     | Used with the content property to generate content after the initial content of an element.  |  h1::after { content: "+" } places a plus-sign at the end of a top-level heading   |
