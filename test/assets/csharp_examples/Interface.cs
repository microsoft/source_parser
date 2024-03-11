
using System;
namespace Equal{
    interface IEquatable<T>
    {
        bool Equals(T obj);
    }

    public interface ISampleInterface
    {
        // Property declaration:
        string Name
        {
            get;
            set;
        }
    }

    public class Car : IEquatable<Car>, Other.ISampleInterface
    {
        public string Name
        {
            get { return "Employee Name"; }
            set { }
        }

        // Implementation of IEquatable<T> interface
        public bool Equals(Car car)
        {
            return (this.Make, this.Model, this.Year) ==
                (car.Make, car.Model, car.Year);
        }
    }
}