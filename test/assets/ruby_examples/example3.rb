# define original class
class Example

    def say_hello
        puts "hello"
    end

    end

# re-open the class
class Example

    # add new functionality
    def do_stuff
        puts "doing stuff"
    end

end

# usage
Example.new.say_hello # => hello
Example.new.do_stuff # => doing stuff

# other ways to reopen the class

# open the instance of the class definition
Example.instance_eval do
end

# open the eigenclass
# you need to understand Ruby's object model 
# to fully understand what the eigenclass is
class << Example
end

# syntactic sugar for class << Example
Example.class_eval do
end