// Illustrative failing reproduction for the /dotnet-ai.fix TDD loop.
// Self-contained: a tiny buggy SUT plus the test that captures the symptom.
// Step 1 (Reproduce) — this [Fact] is RED because Add has an off-by-one bug.
// Step 2 (Fix) — change `a + b + 1` to `a + b`; the test goes green.
using Xunit;

namespace DotnetAiKit.Examples.Fix
{
    // Symptom: summing two numbers returns a result that is one too high.
    public sealed class Calculator
    {
        public int Add(int a, int b) => a + b + 1; // BUG: stray +1
    }

    public sealed class FailingReproTest
    {
        [Fact]
        public void Add_ReturnsSumOfOperands()
        {
            // Arrange
            var calculator = new Calculator();

            // Act
            int result = calculator.Add(2, 3);

            // Assert — reproduces the reported symptom (expected 5, actual 6).
            Assert.Equal(5, result);
        }
    }
}
