# frozen_string_literal: true
require_relative "custom_rule_helpers"

module ERBLint
  module Linters
    class DetailsMenuDoesntHaveSrc < Linter
      include LinterRegistry
      include ERBLint::Linters::CustomRuleHelpers

      MESSAGE = "Details Menus can't have src attributes"

      def run(processed_source)
        tags(processed_source).each do |tag|
          next if tag.name != "details-menu"
          next if tag.closing?
          next if !tag.attributes['src']

          generate_offense(self.class, processed_source, tag)
        end

        is_rule_disabled?(processed_source)
      end
    end
  end
end