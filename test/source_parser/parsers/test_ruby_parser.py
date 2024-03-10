# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.parsers import RubyParser

DIR = "test/assets/ruby_examples/"


def create_ruby_parser(source):
    with open(source, 'r', encoding='utf-8') as file:
        rp = RubyParser(file.read())
    return rp


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "example.rb",
            [
                'require "#{Rails.root}/config/environment"',
                'require "slop"',
            ],
        ),
        (
            DIR + "example2.rb",
            [
                'require_relative "custom_rule_helpers"',
            ],
        ),
    ],
)
def test_context(source, target):
    rp = create_ruby_parser(source)
    assert rp.schema["contexts"] == target


def test_classes():
    source = DIR + "example.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']
    assert len(classes) == 4

    cl1 = classes[0]
    cl2 = classes[2]
    cl3 = classes[3]
    cl4 = classes[1]

    assert cl1["name"] == "CredentialNormalization"
    assert cl1["definition"] == "    class CredentialNormalization < Transition"
    assert cl1["attributes"]["namespace_prefix"] == "A.B."
    assert cl1["attributes"]["bases"] == ["Transition"]
    assert cl1["attributes"]["attribute_expressions"] == [
        "      attr_reader :unverified_total",
        "      PROCESS_BATCH_SIZE = 10000",
        "      CREATE_BATCH_SIZE = 1000",
        "      CLEANUP_BATCH_SIZE = 1000",
    ]

    assert cl2["name"] == "RegistrationsVerifier"
    assert cl2["definition"] == "      class RegistrationsVerifier"
    assert cl2["attributes"]["namespace_prefix"] == "A.B."
    assert cl2["attributes"]["bases"] == []
    assert cl2["attributes"]["attribute_expressions"] == []

    assert cl3["name"] == "RegistrationCleaner"
    assert cl3["definition"] == "      class RegistrationCleaner"
    assert cl3["attributes"]["namespace_prefix"] == "A.B."
    assert cl3["attributes"]["bases"] == []
    assert cl3["attributes"]["attribute_expressions"] == []

    assert cl4["name"] == "BackfillRepositoryVulnerabilityAlertsActiveTransition"
    assert cl4["definition"] == "    class BackfillRepositoryVulnerabilityAlertsActiveTransition < ActiveRecord::Migration[7.1]"
    assert cl4["attributes"]["namespace_prefix"] == "A.B."
    assert cl4["attributes"]["bases"] == ["ActiveRecord::Migration[7.1]"]
    assert cl4["attributes"]["attribute_expressions"] == []


def test_methods():
    source = DIR + "example.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    cl1 = classes[0]
    cl2 = classes[2]
    cl3 = classes[3]
    cl4 = classes[1]

    m1, m2, m3, m4 = cl1["methods"]
    assert m1["name"] == "after_initialize"
    assert m1["signature"] == '      def after_initialize(file, data, mode="w")'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == ['file', 'data', 'mode="w"']

    assert m2["name"] == "perform"
    assert m2["signature"] == '      def perform'
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["parameters"] == []

    assert m3["name"] == "process"
    assert m3["signature"] == '      def process(rows)'
    assert m3["attributes"]["namespace_prefix"] == ""
    assert m3["attributes"]["parameters"] == ["rows"]

    assert m4["name"] == "run_registrations_verification"
    assert m4["signature"] == '      def run_registrations_verification(rows)'
    assert m4["attributes"]["namespace_prefix"] == ""
    assert m4["attributes"]["parameters"] == ["rows"]

    m1, m2 = cl2["methods"]
    assert m1["name"] == "verify"
    assert m1["signature"].strip() == 'def self.verify(two_factor_credential)'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == ["two_factor_credential"]

    assert m2["name"] == "verify_sms_backup_registration"
    assert m2["signature"].strip() == 'def self.verify_sms_backup_registration(two_factor_credential)'
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["parameters"] == ["two_factor_credential"]

    m1 = cl3["methods"][0]
    assert m1["name"] == "clean_registrations"
    assert m1["signature"].strip() == 'def self.clean_registrations(user_ids)'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == ["user_ids"]

    m1 = cl4["methods"][0]
    assert m1["name"] == "up"
    assert m1["signature"].strip() == 'def self.up'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == []


def test_nested_class():
    source = DIR + "example.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    cl = classes[0]

    cl1 = cl["classes"][0]
    assert cl1["name"] == "RegistrationsVerifier"
    assert cl1["attributes"]["namespace_prefix"] == "A.B."
    assert cl1["attributes"]["bases"] == []

    cl2 = cl["classes"][1]
    assert cl2["name"] == "RegistrationCleaner"
    assert cl2["attributes"]["namespace_prefix"] == "A.B."
    assert cl2["attributes"]["bases"] == []


def test_include():
    source = DIR + "example2.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    cl = classes[0]

    assert cl["attributes"]["contexts"] == ["LinterRegistry", "ERBLint.Linters.CustomRuleHelpers"]


def test_open_classes():
    source = DIR + "example3.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    assert len(classes) == 1

    cl = classes[0]

    m1, m2 = cl["methods"]
    assert m1["name"] == "say_hello"
    assert m1["signature"].strip() == 'def say_hello'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == []

    assert m2["name"] == "do_stuff"
    assert m2["signature"].strip() == 'def do_stuff'
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["parameters"] == []


def test_module_level_methods():
    '''
    This unit test tests module-level method
    '''
    source = DIR + "example4.rb"
    rp = create_ruby_parser(source)

    methods = rp.schema['methods']

    assert len(methods) == 2

    m1 = methods[0]
    m2 = methods[1]

    assert m1["name"] == "is_counter_correct?"
    assert m1["signature"].strip() == 'def is_counter_correct?(processed_source)'
    assert m1["attributes"]["namespace_prefix"] == "A.B.C."
    assert m1["attributes"]["parameters"] == ["processed_source"]

    assert m2["name"] == "is_rule_disabled?"
    assert m2["signature"].strip() == 'def is_rule_disabled?(processed_source)'
    assert m2["attributes"]["namespace_prefix"] == "A.B.C."
    assert m2["attributes"]["parameters"] == ["processed_source"]


def test_class_level_methods():
    '''
    This unit test tests module-level method
    '''
    source = DIR + "example5.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    assert len(classes) == 1

    cl = classes[0]

    m1, m2 = cl["methods"]
    assert m1["name"] == "up"
    assert m1["signature"].strip() == 'def self.up'
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["parameters"] == []

    assert m2["name"] == "down"
    assert m2["signature"].strip() == 'def self.down'
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["parameters"] == []


def test_single_module():
    '''
    This unit test tests parsing of single module
    '''
    source = DIR + "example6.rb"
    rp = create_ruby_parser(source)

    methods = rp.schema['methods']

    assert len(methods) == 6

    m1 = methods[0]
    m2 = methods[1]
    m3 = methods[2]
    m4 = methods[3]
    m5 = methods[4]
    m6 = methods[5]

    assert m1["name"] == "assert_optimizely_experiments"
    assert m1["signature"].strip() == 'def assert_optimizely_experiments(experiments: {}, tracks: {}, activation: false, activation_calls: 1, &block)'
    assert m1["attributes"]["namespace_prefix"] == "ExperimentTestHelper."

    assert m2["name"] == "stub_optimizely_experiments"
    assert m2["signature"].strip() == 'def stub_optimizely_experiments(experiments: {}, activation: false, activation_calls: 1, &block)'
    assert m2["attributes"]["namespace_prefix"] == "ExperimentTestHelper."

    assert m3["name"] == "assert_no_optimizely_call"
    assert m3["signature"].strip() == 'def assert_no_optimizely_call(experiments: {}, tracks: {}, &block)'
    assert m3["attributes"]["namespace_prefix"] == "ExperimentTestHelper."

    assert m4["name"] == "assert_no_optimizely_track_calls"
    assert m4["signature"].strip() == 'def assert_no_optimizely_track_calls(tracks: {}, &block)'
    assert m4["attributes"]["namespace_prefix"] == "ExperimentTestHelper."

    assert m5["name"] == "stub_subject_activated"
    assert m5["signature"].strip() == 'def stub_subject_activated(activation)'
    assert m5["attributes"]["namespace_prefix"] == "ExperimentTestHelper."
    assert m5["attributes"]["parameters"] == ["activation"]

    assert m6["name"] == "assert_hydro_click_attributes"
    assert m6["signature"].strip() == 'def assert_hydro_click_attributes(element:, event_name:, tags:)'
    assert m6["attributes"]["namespace_prefix"] == "ExperimentTestHelper."


def test_single_module_with_class():
    '''
    This unit test tests parsing of single module
    '''
    source = DIR + "example7.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    assert len(classes) == 1

    cl = classes[0]

    assert cl["name"] == "TestHelper"
    assert cl["definition"] == "    class TestHelper"
    assert cl["attributes"]["namespace_prefix"] == "ExperimentTestHelper."

    m1, m2, m3, m4, m5, m6 = cl["methods"]

    assert m1["name"] == "assert_optimizely_experiments"
    assert m1["signature"].strip() == 'def assert_optimizely_experiments(experiments: {}, tracks: {}, activation: false, activation_calls: 1, &block)'
    assert m1["attributes"]["namespace_prefix"] == ""

    assert m2["name"] == "stub_optimizely_experiments"
    assert m2["signature"].strip() == 'def stub_optimizely_experiments(experiments: {}, activation: false, activation_calls: 1, &block)'
    assert m2["attributes"]["namespace_prefix"] == ""

    assert m3["name"] == "assert_no_optimizely_call"
    assert m3["signature"].strip() == 'def assert_no_optimizely_call(experiments: {}, tracks: {}, &block)'
    assert m3["attributes"]["namespace_prefix"] == ""

    assert m4["name"] == "assert_no_optimizely_track_calls"
    assert m4["signature"].strip() == 'def assert_no_optimizely_track_calls(tracks: {}, &block)'
    assert m4["attributes"]["namespace_prefix"] == ""

    assert m5["name"] == "stub_subject_activated"
    assert m5["signature"].strip() == 'def stub_subject_activated(activation)'
    assert m5["attributes"]["namespace_prefix"] == ""
    assert m5["attributes"]["parameters"] == ["activation"]

    assert m6["name"] == "assert_hydro_click_attributes"
    assert m6["signature"].strip() == 'def assert_hydro_click_attributes(element:, event_name:, tags:)'
    assert m6["attributes"]["namespace_prefix"] == ""


def test_class_in_condition_case():
    '''
    This unit test tests parsing of single module
    '''
    source = DIR + "example8.rb"
    rp = create_ruby_parser(source)

    classes = rp.schema['classes']

    assert len(classes) == 1

    cl = classes[0]

    assert cl["name"] == "SearchDotcomTopicResultViewTest"
    assert cl["definition"] == "  class SearchDotcomTopicResultViewTest < TestCase"
    assert cl["attributes"]["namespace_prefix"] == ""

    assert len(cl["methods"]) == 1

    m1 = cl["methods"][0]

    assert m1["name"] == "new_view"
    assert m1["signature"] == '    def new_view(topic)'
    assert m1["attributes"]["namespace_prefix"] == ""
