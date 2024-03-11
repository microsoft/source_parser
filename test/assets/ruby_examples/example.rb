require "#{Rails.root}/config/environment"
require "slop"
      
module A
  module B
    class CredentialNormalization < Transition
      attr_reader :unverified_total

      PROCESS_BATCH_SIZE = 10000
      CREATE_BATCH_SIZE = 1000
      CLEANUP_BATCH_SIZE = 1000

      def after_initialize(file, data, mode="w")
        @cleanup_only = @other_args[:cleanup_only]
        if @cleanup_only
          raise ArgumentError, "Cannot use --cleanup_only without --write"
        end
        @unverified_total = 0
      end

      # Returns nothing.
      def perform
        log "Finished transition for min_id: #{@min_id} to max_id: #{@max_id}"
        log "Total unverified rows found during transition: #{@unverified_total}"
      end

      private

      def process(rows)
        return if dry_run? || unverified_rows.empty?

        run_registrations_cleanup(unverified_rows)
        return if @cleanup_only
      end

      # verifies that the given two_factor_credential rows have expected sms_registration and totp_app_registration rows
      # returns unverified rows
      def run_registrations_verification(rows)
        rows.filter do |row|
          !verified
        end
      end

      class RegistrationsVerifier
        def self.verify(two_factor_credential)
            verified_totp_app && verified_backup
        end

        # verifies the given two_factor_credential row has a backup sms_registration row
        # returns true if verified, false otherwise
        def self.verify_sms_backup_registration(two_factor_credential)
          true
        end
      end

      class RegistrationCleaner
        def self.clean_registrations(user_ids)
          return 0 unless user_ids.present?
        end
      end
    end

    class BackfillRepositoryVulnerabilityAlertsActiveTransition < ActiveRecord::Migration[7.1]
      def self.up
        return
      end
    end
  end
end

if $0 == __FILE__
  options = slop.to_hash
  options = options.merge(dry_run: !options[:write])

  transition = A::B::CredentialNormalization.new(**options)
  transition.run
end
