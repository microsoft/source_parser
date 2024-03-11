# typed: false
# frozen_string_literal: true

module ExperimentTestHelper
    # Meant to wrap tests to expect optimizely and OptimizelyExperiment behaviors
    #   Use when using OptimizelyExperiment to implement experiment in test
    
    class TestHelper
        def assert_optimizely_experiments(experiments: {}, tracks: {}, activation: false, activation_calls: 1, &block)
            return 
        end
    
        # Meant to wrap tests to stub optimizely and OptimizelyExperiment behaviors
        #   Use when using OptimizelyExperiment to implement experiment in test
    
        def stub_optimizely_experiments(experiments: {}, activation: false, activation_calls: 1, &block)
            return
        end
    
        # Meant to wrap tests to expect no optimizely calls at all or just no calls to the experiments provided
        def assert_no_optimizely_call(experiments: {}, tracks: {}, &block)
            return
        end
    
        def assert_no_optimizely_track_calls(tracks: {}, &block)
            yield
        end
    
        def stub_subject_activated(activation)
            yield
        end
    
        def assert_hydro_click_attributes(element:, event_name:, tags:)
            refute_nil element[\"data-hydro-click-hmac\"]
        end
    end
  end