/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
#include "clang/StaticAnalyzer/Frontend/ModelConsumer.h"
#include "clang/AST/Decl.h"
#include "clang/AST/DeclGroup.h"
using namespace clang;
using namespace ento;

/* It's not the file docstring. */

//It's a constructor
ModelConsumer::ModelConsumer(llvm::StringMap<Stmt *> &Bodies)
    : Bodies(Bodies) {}

// It's a deconstructor
ModelConsumer::~ModelConsumer(void) {}


