require "test_helper"

if A.enterprise?
  class SearchDotcomTopicResultViewTest < TestCase
    def new_view(topic)
      hash = {
        "created_at" => topic.created_at.iso8601,
        "updated_at" => topic.updated_at.iso8601,
        "display_name" => topic.display_name,
        "name" => topic.name,
        "created_by" => topic.created_by,
        "description" => topic.description,
        "short_description" => topic.short_description,
        "released" => topic.released,
        "featured" => topic.featured?,
        "curated" => topic.curated?,
        "repository_count" => topic.applied_repository_topics.count,
        "aliases" => topic.topic_aliases.map { |t| {"topic_relation" => t.attributes} },
        "related" => topic.related_topics.map { |t| {"topic_relation" => t.attributes} },
        "logo_url" => topic.logo_url,
        "text_matches" => [],
      }
      Search::DotcomTopicResultView.new(hash)
    end

    context "#related_topic_names" do
      test "returns names of topic aliases and related topics" do
        topic = create :topic
        alias_relation = create(:topic_relation, topic: topic, relation_type: :alias)
        related_relation = create(:topic_relation, topic: topic, relation_type: :related)
        view = new_view(topic)

        assert_same_elements [alias_relation.name, related_relation.name], view.related_topic_names
      end
    end
end