// This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
// https://gitlab.com/sosy-lab/benchmarking/sv-lib
//
// SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers
//
// SPDX-License-Identifier: Apache-2.0
/*
<num>      ::=  positive unsigned integer (greater than zero)
<uint>     ::=  unsigned integer (including zero)
<string>   ::=  sequence of whitespace and printable characters without '\n'
<symbol>   ::=  sequence of printable characters without '\n'
<comment>  ::=  ';' <string>
<nid>      ::=  <num>
<sid>      ::=  <num>
<const>    ::=  'const' <sid> [0-1]+
<constd>   ::=  'constd' <sid> ['-']<uint>
<consth>   ::=  'consth' <sid> [0-9a-fA-F]+
<input>    ::=  ('input' | 'one' | 'ones' | 'zero') <sid>
              | <const>
              | <constd>
              | <consth>
<state>    ::=  'state' <sid>
<bitvec>   ::=  'bitvec' <num>
<array>    ::=  'array' <sid> <sid>
<node>     ::=  <sid> 'sort' (<array> | <bitvec>)
              | <nid> (<input> | <state>)
              | <nid> <opidx> <sid> <nid> <uint> [<uint>]
              | <nid> <op> <sid> <nid> [<nid> [<nid>]]
              | <nid> ('init' | 'next') <sid> <nid> <nid>
              | <nid> ('bad' | 'constraint' | 'fair' | 'output') <nid>
              | <nid> 'justice' <num> (<nid>)+
<line>     ::=  <comment>
              | <node> [<symbol>] [<comment>]
<btor>     ::=  (<line>'\n')+
*/



grammar Btor2;

//
// Lexer
//

COMMENT : ';' ~[\r\n]* -> skip;
WHITESPACE : [ \t]+ -> skip;

// Keywords
CONSTD : 'constd';
CONSTH : 'consth';
CONST : 'const';


// Input
INPUT : 'input';
ONES : 'ones';
ONE : 'one';
ZERO : 'zero';

// Sorts
SORT : 'sort';
BITVEC : 'bitvec';
ARRAY : 'array';

STATE : 'state';

// Prop keywords
BAD : 'bad';
CONSTRAINT : 'constraint';
FAIR : 'fair';
OUTPUT : 'output';

JUSTICE : 'justice';

INIT : 'init';
NEXT : 'next';

// Indexed Operations
SEXT : 'sext';
UEXT : 'uext';
SLICE : 'slice';

// Unary Operations
NOT : 'not';
INC : 'inc';
DEC : 'dec';
NEG : 'neg';
REDAND : 'redand';
REDOR : 'redor';
REDXOR : 'redxor';

// Binary Operations
IFF : 'iff';
IMPLIES : 'implies';
EQ : 'eq'; NEQ : 'neq';
SGT : 'sgt'; UGT : 'ugt';
SGTE : 'sgte'; UGTE : 'ugte';
SLT : 'slt'; ULT : 'ult';
SLTE : 'slte'; ULTE : 'ulte';
AND : 'and'; NAND : 'nand';
OR : 'or'; NOR : 'nor';
XOR : 'xor'; XNOR : 'xnor';
ROL : 'rol'; ROR : 'ror';
SLL : 'sll';
SRA : 'sra'; SRL : 'srl';
ADD : 'add'; SUB : 'sub'; MUL : 'mul';
SDIV : 'sdiv'; UDIV : 'udiv';
SMOD : 'smod'; SREM : 'srem'; UREM : 'urem';
SADDO : 'saddo'; UADDO : 'uaddo';
SDIVO : 'sdivo';
SMULO : 'smulo'; UMULO : 'umulo';
SSUBO : 'ssubo'; USUBO : 'usubo';
CONCAT : 'concat';
READ : 'read';

// Ternary Operations
ITE : 'ite';
WRITE : 'write';

NEG_SYM : '-';

// Types
NUM : NEG_SYM?[1-9][0-9]*;
ZERO_LITERAL : '0';
SYMBOL : [a-zA-Z_!@#$%^&*+=?/~(){}\\<>\-.[:\]][a-zA-Z0-9_!@#$%^&*+=?/~\\(){}<>\-.[:\]]*;
BINARY : [01]+;
HEX : [0-9a-fA-F]+;
NEWLINE : [\r\n]+;


//
// Parser
//

uint : ZERO_LITERAL | NUM ;

btor2_file
    : NEWLINE* (line NEWLINE+)* line? EOF
    ;

line
    : NUM node
    ;

node
    : sortNode
    | input
    | stateNode
    | indexedOpNode symbol?
    | ternaryOpNode symbol?
    | unaryOpNode symbol?
    | binaryOpNode symbol?
    | initNode
    | nextNode
    | propNode
    | justiceNode
    ;

symbol
    : SYMBOL
    | INPUT | ONE | ONES | ZERO
    | SORT | BITVEC | ARRAY | STATE
    | BAD | CONSTRAINT | FAIR | OUTPUT | JUSTICE
    | INIT | NEXT
    | CONST | CONSTD | CONSTH
    | SEXT | UEXT | SLICE
    | NOT | INC | DEC | NEG | REDAND | REDOR | REDXOR
    | IFF | IMPLIES | EQ | NEQ
    | SGT | UGT | SGTE | UGTE | SLT | ULT | SLTE | ULTE
    | AND | NAND | OR | NOR | XOR | XNOR
    | ROL | ROR | SLL | SRA | SRL
    | ADD | SUB | MUL | SDIV | UDIV | SMOD | SREM | UREM
    | SADDO | UADDO | SDIVO | SMULO | UMULO | SSUBO | USUBO
    | CONCAT | READ | ITE | WRITE
    ;

input
    : inputLiteral
    | constNode
    ;

inputLiteral
    : (INPUT | ONE | ONES | ZERO) NUM SYMBOL?;

stateNode
    : STATE NUM SYMBOL?
    ;

constNode
    : CONST NUM binaryValue
    | CONSTD NUM NEG_SYM? uint
    | CONSTH NUM HEX
    ;

binaryValue
    : (BINARY | ZERO_LITERAL | NUM)
    ;

indexedOpNode
    : (SEXT | UEXT) NUM NUM uint
    | SLICE NUM NUM uint uint
    ;

unaryOpNode
    : (NOT | INC | DEC | NEG | REDAND | REDOR | REDXOR) NUM NUM
    ;

binaryOpNode
    : binaryOpNodeFixed
    | binaryOpNodeVar
    ;

binaryOpNodeFixed
    : (AND | NAND | OR | NOR | XOR | XNOR
       | IFF | IMPLIES | EQ | NEQ
       | SGT | UGT | SGTE | UGTE
       | SLT | ULT | SLTE | ULTE
       | ADD | SUB | MUL | SDIV | UDIV | SMOD | SREM | UREM
       | SADDO | UADDO | SDIVO | SMULO | UMULO | SSUBO | USUBO
       | ROL | ROR | SLL | SRA | SRL
       )
      NUM NUM NUM
    ;

binaryOpNodeVar
    : (CONCAT | READ) NUM NUM (NUM (NUM)?)?
    ;

ternaryOpNode
    : (ITE | WRITE) NUM NUM NUM NUM
    ;

initNode
    : INIT NUM NUM NUM
    ;

nextNode
    : NEXT NUM NUM NUM
    ;

propNode
    : (BAD | CONSTRAINT | OUTPUT | FAIR) NUM symbol?
    ;

justiceNode
    : JUSTICE uint NUM+
    ;

sortNode
    : SORT (bitvec | array)
    ;

bitvec
    : BITVEC NUM
    ;

array
    : ARRAY NUM NUM
    ;