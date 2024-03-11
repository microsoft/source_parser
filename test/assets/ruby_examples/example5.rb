# frozen_string_literal: true

require "transitions/archived_deployment_statuses"

class BackfillRepositoryIdOnArchivedDeploymentStatusesTransition < ActiveRecord::Migration[7.0]
  def self.up
    return if !Rails.development?
  end

  def self.down
  end
end