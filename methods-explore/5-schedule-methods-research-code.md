<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I had this problem of trying to schedule work for larger projects for my team over the course of the year. Some things are known, some things are not. These are major projects, things that take two to six months to complete and require multiple staff to complete from different teams, so this work is really important. That way I know what capacity we have for the rest of the year.

Right now, I'm kind of experimenting with Monte Carlo simulations, just being able to give ranges of what I think could be what our past projects have been like and their size and scope. Are there more sophisticated, better ways of estimating the level of work going forward? That way I can really dial in what we have available. Could you research maybe at least three to five different methods and associate Python code with each to give me a taste of what's going on?

Based on my research, I've identified five sophisticated methods that go beyond basic Monte Carlo simulation for project capacity planning and resource scheduling. Let me provide you with comprehensive information and Python implementations for each.

## Five Advanced Project Capacity Planning Methods

### 1. **PERT (Program Evaluation and Review Technique) with Three-Point Estimation**

PERT uses optimistic, most likely, and pessimistic estimates to create probability distributions for project durations. Unlike simple Monte Carlo, it leverages beta distributions and identifies critical paths with probabilistic completion times[^1_1][^1_2].

**When to use:** When you have historical data providing ranges for task durations and need to understand completion probabilities.

**Python Implementation:**

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

class PERTAnalysis:
    def __init__(self, activities, optimistic, likely, pessimistic, predecessors):
        """
        PERT Analysis with three-point estimation
        
        Parameters:
        - activities: list of activity names
        - optimistic: list of optimistic durations
        - likely: list of most likely durations
        - pessimistic: list of pessimistic durations
        - predecessors: list of predecessor activities (comma-separated strings)
        """
        self.activities = activities
        self.optimistic = np.array(optimistic)
        self.likely = np.array(likely)
        self.pessimistic = np.array(pessimistic)
        self.predecessors = predecessors
        
        # Calculate expected time and variance using PERT formula
        self.expected_time = (optimistic + 4 * likely + pessimistic) / 6
        self.variance = ((pessimistic - optimistic) / 6) ** 2
        self.std_dev = np.sqrt(self.variance)
        
    def calculate_critical_path(self):
        """Calculate critical path using forward and backward pass"""
        n = len(self.activities)
        
        # Initialize times
        self.early_start = np.zeros(n)
        self.early_finish = np.zeros(n)
        self.late_start = np.zeros(n)
        self.late_finish = np.zeros(n)
        
        # Forward pass
        for i in range(n):
            if self.predecessors[i] == '-':
                self.early_start[i] = 0
            else:
                pred_list = [self.activities.index(p.strip()) 
                            for p in self.predecessors[i].split(',')]
                self.early_start[i] = max(self.early_finish[j] for j in pred_list)
            
            self.early_finish[i] = self.early_start[i] + self.expected_time[i]
        
        # Project duration
        project_duration = max(self.early_finish)
        
        # Backward pass
        self.late_finish = np.full(n, project_duration)
        for i in range(n-1, -1, -1):
            # Find successors
            successors = []
            for j, pred in enumerate(self.predecessors):
                if pred != '-' and self.activities[i] in pred:
                    successors.append(j)
            
            if successors:
                self.late_finish[i] = min(self.late_start[j] for j in successors)
            
            self.late_start[i] = self.late_finish[i] - self.expected_time[i]
        
        # Calculate slack
        self.slack = self.late_start - self.early_start
        
        # Identify critical path
        self.critical_path = [self.activities[i] for i in range(n) 
                             if abs(self.slack[i]) < 0.01]
        
        # Critical path variance (sum of variances on critical path)
        critical_indices = [i for i in range(n) if abs(self.slack[i]) < 0.01]
        self.critical_path_variance = sum(self.variance[i] for i in critical_indices)
        self.critical_path_std = np.sqrt(self.critical_path_variance)
        
        return project_duration
    
    def probability_of_completion(self, target_duration):
        """Calculate probability of completing project by target duration"""
        project_duration = max(self.early_finish)
        z_score = (target_duration - project_duration) / self.critical_path_std
        probability = stats.norm.cdf(z_score)
        return probability
    
    def monte_carlo_simulation(self, n_simulations=10000):
        """Run Monte Carlo simulation using PERT distributions"""
        durations = []
        
        for _ in range(n_simulations):
            # Sample from beta distribution for each activity
            sampled_durations = []
            for i in range(len(self.activities)):
                # Beta distribution parameters
                alpha = (self.expected_time[i] - self.optimistic[i]) / \
                       (self.pessimistic[i] - self.optimistic[i]) * 4
                beta_param = 4 - alpha
                
                # Sample and scale
                sample = np.random.beta(alpha, beta_param)
                scaled_duration = self.optimistic[i] + sample * \
                                 (self.pessimistic[i] - self.optimistic[i])
                sampled_durations.append(scaled_duration)
            
            # Calculate critical path for this iteration
            temp_expected = self.expected_time.copy()
            self.expected_time = np.array(sampled_durations)
            duration = self.calculate_critical_path()
            durations.append(duration)
            self.expected_time = temp_expected
        
        return np.array(durations)
    
    def get_summary(self):
        """Return summary DataFrame"""
        df = pd.DataFrame({
            'Activity': self.activities,
            'Optimistic': self.optimistic,
            'Likely': self.likely,
            'Pessimistic': self.pessimistic,
            'Expected': self.expected_time,
            'Std Dev': self.std_dev,
            'Early Start': self.early_start,
            'Early Finish': self.early_finish,
            'Late Start': self.late_start,
            'Late Finish': self.late_finish,
            'Slack': self.slack,
            'Critical': ['Yes' if s < 0.01 else 'No' for s in self.slack]
        })
        return df

# Example usage
activities = ['A', 'B', 'C', 'D', 'E', 'F']
optimistic = [40, 54, 58, 32, 26, 44]
likely = [50, 60, 70, 40, 30, 50]
pessimistic = [60, 66, 82, 48, 34, 56]
predecessors = ['-', 'A', 'A', 'B', 'C', 'D,E']

pert = PERTAnalysis(activities, optimistic, likely, pessimistic, predecessors)
duration = pert.calculate_critical_path()

print(f"Expected Project Duration: {duration:.2f} days")
print(f"Critical Path: {' → '.join(pert.critical_path)}")
print(f"\nProbability of completion within:")
for target in [duration - 10, duration, duration + 10]:
    prob = pert.probability_of_completion(target)
    print(f"  {target:.0f} days: {prob*100:.1f}%")

# Run Monte Carlo simulation
simulated_durations = pert.monte_carlo_simulation(10000)
print(f"\nMonte Carlo Results (10,000 simulations):")
print(f"  Mean: {np.mean(simulated_durations):.2f}")
print(f"  P50: {np.percentile(simulated_durations, 50):.2f}")
print(f"  P85: {np.percentile(simulated_durations, 85):.2f}")
print(f"  P95: {np.percentile(simulated_durations, 95):.2f}")
```


***

### 2. **Resource-Constrained Project Scheduling (RCPSP) with Optimization**

Unlike CPM which assumes unlimited resources, RCPSP optimally schedules tasks considering actual resource constraints—critical for multi-team environments[^1_3][^1_4].

**When to use:** When you have limited resources (people, equipment) that must be shared across multiple projects and tasks.

**Python Implementation:**

```python
from pulp import *
import pandas as pd
import numpy as np
from itertools import product

class ResourceConstrainedScheduler:
    def __init__(self, tasks, durations, resource_requirements, 
                 resource_capacities, predecessors, planning_horizon=None):
        """
        Resource-Constrained Project Scheduling
        
        Parameters:
        - tasks: list of task names
        - durations: list of task durations
        - resource_requirements: dict of {task: {resource: amount}}
        - resource_capacities: dict of {resource: max_capacity}
        - predecessors: dict of {task: [predecessor_tasks]}
        - planning_horizon: max time (calculated if None)
        """
        self.tasks = tasks
        self.n_tasks = len(tasks)
        self.durations = {tasks[i]: durations[i] for i in range(len(tasks))}
        self.resource_req = resource_requirements
        self.resource_cap = resource_capacities
        self.predecessors = predecessors
        
        # Calculate planning horizon (upper bound)
        if planning_horizon is None:
            self.horizon = sum(durations)
        else:
            self.horizon = planning_horizon
        
        self.model = None
        self.start_times = None
        
    def build_model(self):
        """Build the optimization model"""
        # Create the model
        self.model = LpProblem("RCPSP", LpMinimize)
        
        # Decision variables: binary variable for each task-time combination
        self.x = {}
        for j in range(self.n_tasks):
            for t in range(self.horizon + 1):
                self.x[j, t] = LpVariable(f"x_{self.tasks[j]}_{t}", cat='Binary')
        
        # Completion time variable (to minimize)
        self.makespan = LpVariable("makespan", lowBound=0, cat='Continuous')
        
        # Objective: Minimize makespan
        self.model += self.makespan, "Minimize_Makespan"
        
        # Constraint 1: Each task starts exactly once
        for j in range(self.n_tasks):
            self.model += (
                lpSum(self.x[j, t] for t in range(self.horizon + 1)) == 1,
                f"Start_Once_{self.tasks[j]}"
            )
        
        # Constraint 2: Precedence relationships
        for j, task in enumerate(self.tasks):
            if task in self.predecessors:
                for pred in self.predecessors[task]:
                    pred_idx = self.tasks.index(pred)
                    # Successor must start after predecessor finishes
                    self.model += (
                        lpSum(t * self.x[j, t] for t in range(self.horizon + 1)) >=
                        lpSum((t + self.durations[pred]) * self.x[pred_idx, t] 
                             for t in range(self.horizon + 1)),
                        f"Precedence_{pred}_to_{task}"
                    )
        
        # Constraint 3: Resource capacity constraints
        resources = list(self.resource_cap.keys())
        for r in resources:
            for t in range(self.horizon + 1):
                # Sum of resource usage at time t cannot exceed capacity
                resource_usage = []
                for j, task in enumerate(self.tasks):
                    if task in self.resource_req and r in self.resource_req[task]:
                        # Task uses resource if it started within its duration window
                        for t2 in range(max(0, t - self.durations[task] + 1), t + 1):
                            resource_usage.append(
                                self.resource_req[task][r] * self.x[j, t2]
                            )
                
                if resource_usage:
                    self.model += (
                        lpSum(resource_usage) <= self.resource_cap[r],
                        f"Resource_{r}_Time_{t}"
                    )
        
        # Constraint 4: Makespan definition
        for j, task in enumerate(self.tasks):
            self.model += (
                self.makespan >= lpSum((t + self.durations[task]) * self.x[j, t] 
                                      for t in range(self.horizon + 1)),
                f"Makespan_{task}"
            )
    
    def solve(self, solver=None):
        """Solve the optimization problem"""
        if self.model is None:
            self.build_model()
        
        # Solve
        if solver is None:
            solver = PULP_CBC_CMD(msg=1, timeLimit=300)
        
        self.model.solve(solver)
        
        # Extract solution
        if LpStatus[self.model.status] == 'Optimal':
            self.start_times = {}
            for j, task in enumerate(self.tasks):
                for t in range(self.horizon + 1):
                    if value(self.x[j, t]) > 0.5:
                        self.start_times[task] = t
                        break
            
            self.project_duration = value(self.makespan)
            return True
        else:
            return False
    
    def get_schedule(self):
        """Return schedule as DataFrame"""
        if self.start_times is None:
            return None
        
        schedule_data = []
        for task in self.tasks:
            schedule_data.append({
                'Task': task,
                'Start': self.start_times[task],
                'Duration': self.durations[task],
                'Finish': self.start_times[task] + self.durations[task],
                'Resources': ', '.join([f"{r}: {amt}" 
                                       for r, amt in self.resource_req.get(task, {}).items()])
            })
        
        df = pd.DataFrame(schedule_data)
        return df.sort_values('Start')
    
    def plot_gantt(self):
        """Create a Gantt chart of the schedule"""
        if self.start_times is None:
            return
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for i, task in enumerate(self.tasks):
            start = self.start_times[task]
            duration = self.durations[task]
            ax.barh(i, duration, left=start, height=0.5, alpha=0.8)
            ax.text(start + duration/2, i, task, 
                   ha='center', va='center', fontsize=9)
        
        ax.set_yticks(range(len(self.tasks)))
        ax.set_yticklabels(self.tasks)
        ax.set_xlabel('Time')
        ax.set_title(f'Resource-Constrained Project Schedule (Duration: {self.project_duration:.0f})')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        return fig

# Example usage
tasks = ['A', 'B', 'C', 'D', 'E', 'F']
durations = [3, 4, 2, 5, 3, 2]

# Resource requirements: {task: {resource: amount}}
resource_requirements = {
    'A': {'engineers': 2, 'equipment': 1},
    'B': {'engineers': 3, 'equipment': 2},
    'C': {'engineers': 1, 'equipment': 1},
    'D': {'engineers': 2, 'equipment': 1},
    'E': {'engineers': 2, 'equipment': 2},
    'F': {'engineers': 1, 'equipment': 1}
}

# Resource capacities
resource_capacities = {'engineers': 4, 'equipment': 2}

# Precedence relationships
predecessors = {
    'B': ['A'],
    'C': ['A'],
    'D': ['B'],
    'E': ['C'],
    'F': ['D', 'E']
}

# Solve
scheduler = ResourceConstrainedScheduler(
    tasks, durations, resource_requirements, 
    resource_capacities, predecessors
)
success = scheduler.solve()

if success:
    print(f"Optimal Project Duration: {scheduler.project_duration:.0f} days")
    print("\nOptimal Schedule:")
    print(scheduler.get_schedule())
else:
    print("No optimal solution found")
```


***

### 3. **Bayesian Project Estimation with Historical Data**

Uses Bayesian inference to update project estimates based on historical performance, providing more realistic forecasts that improve over time[^1_5][^1_6].

**When to use:** When you have historical project data and want estimates that learn from past performance and quantify uncertainty.

**Python Implementation:**

```python
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

class BayesianProjectEstimator:
    def __init__(self, prior_mean, prior_std):
        """
        Bayesian estimation for project durations
        
        Parameters:
        - prior_mean: initial belief about average duration
        - prior_std: uncertainty in that belief
        """
        self.prior_mean = prior_mean
        self.prior_std = prior_std
        self.posterior_mean = prior_mean
        self.posterior_std = prior_std
        self.observations = []
        
    def update_with_observation(self, observed_duration, observation_std):
        """
        Update beliefs with new observation using Bayesian updating
        
        Parameters:
        - observed_duration: actual duration observed
        - observation_std: uncertainty in the observation
        """
        # Bayesian update for normal distributions
        prior_precision = 1 / (self.posterior_std ** 2)
        obs_precision = 1 / (observation_std ** 2)
        
        # Posterior precision is sum of precisions
        posterior_precision = prior_precision + obs_precision
        self.posterior_std = np.sqrt(1 / posterior_precision)
        
        # Posterior mean is weighted average
        self.posterior_mean = (prior_precision * self.posterior_mean + 
                              obs_precision * observed_duration) / posterior_precision
        
        self.observations.append({
            'duration': observed_duration,
            'std': observation_std,
            'posterior_mean': self.posterior_mean,
            'posterior_std': self.posterior_std
        })
    
    def update_with_batch(self, historical_durations):
        """Update with multiple historical observations"""
        if len(historical_durations) == 0:
            return
        
        # Estimate observation std from data
        obs_std = np.std(historical_durations)
        if obs_std == 0:
            obs_std = self.prior_std * 0.1
        
        for duration in historical_durations:
            self.update_with_observation(duration, obs_std)
    
    def predict_duration(self, confidence_level=0.95):
        """
        Predict future project duration with confidence interval
        
        Returns: (point_estimate, lower_bound, upper_bound)
        """
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        lower = self.posterior_mean - z_score * self.posterior_std
        upper = self.posterior_mean + z_score * self.posterior_std
        
        return self.posterior_mean, lower, upper
    
    def probability_under_target(self, target_duration):
        """Calculate probability of completing under target"""
        z_score = (target_duration - self.posterior_mean) / self.posterior_std
        return stats.norm.cdf(z_score)
    
    def sample_duration(self, n_samples=1000):
        """Generate samples from posterior distribution"""
        return np.random.normal(self.posterior_mean, self.posterior_std, n_samples)
    
    def plot_evolution(self):
        """Plot how estimates evolved with observations"""
        if not self.observations:
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        n_obs = len(self.observations)
        obs_nums = range(1, n_obs + 1)
        means = [obs['posterior_mean'] for obs in self.observations]
        stds = [obs['posterior_std'] for obs in self.observations]
        
        # Plot mean evolution
        ax1.plot([^1_0] + list(obs_nums), [self.prior_mean] + means, 
                marker='o', label='Posterior Mean')
        ax1.axhline(self.prior_mean, color='r', linestyle='--', 
                   alpha=0.5, label='Prior Mean')
        ax1.fill_between([^1_0] + list(obs_nums),
                        [self.prior_mean - 2*self.prior_std] + 
                        [m - 2*s for m, s in zip(means, stds)],
                        [self.prior_mean + 2*self.prior_std] + 
                        [m + 2*s for m, s in zip(means, stds)],
                        alpha=0.2)
        ax1.set_xlabel('Number of Observations')
        ax1.set_ylabel('Estimated Duration')
        ax1.set_title('Evolution of Duration Estimate')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Plot uncertainty reduction
        ax2.plot([^1_0] + list(obs_nums), [self.prior_std] + stds, 
                marker='s', color='orange')
        ax2.set_xlabel('Number of Observations')
        ax2.set_ylabel('Standard Deviation')
        ax2.set_title('Reduction in Uncertainty')
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        return fig

class BayesianPortfolioPlanner:
    """Plan capacity for portfolio of projects using Bayesian estimates"""
    
    def __init__(self, project_types):
        """
        Initialize with different project types and their estimators
        
        Parameters:
        - project_types: dict of {project_type: BayesianProjectEstimator}
        """
        self.estimators = project_types
        self.portfolio = []
    
    def add_project(self, project_type, start_month, team_size):
        """Add a project to the portfolio"""
        if project_type not in self.estimators:
            raise ValueError(f"Unknown project type: {project_type}")
        
        self.portfolio.append({
            'type': project_type,
            'start_month': start_month,
            'team_size': team_size,
            'estimator': self.estimators[project_type]
        })
    
    def simulate_capacity(self, total_capacity, n_simulations=1000, 
                         planning_horizon=12):
        """
        Simulate capacity utilization over planning horizon
        
        Parameters:
        - total_capacity: total team members available
        - n_simulations: number of Monte Carlo runs
        - planning_horizon: months to plan ahead
        
        Returns: DataFrame with capacity statistics by month
        """
        results = {month: [] for month in range(planning_horizon)}
        
        for _ in range(n_simulations):
            capacity_used = np.zeros(planning_horizon)
            
            for project in self.portfolio:
                # Sample duration for this project
                duration = project['estimator'].sample_duration(1)[^1_0]
                duration_months = int(np.ceil(duration))
                
                start = project['start_month']
                end = min(start + duration_months, planning_horizon)
                
                # Add to capacity usage
                capacity_used[start:end] += project['team_size']
            
            # Record utilization for each month
            for month in range(planning_horizon):
                results[month].append(capacity_used[month] / total_capacity * 100)
        
        # Calculate statistics
        summary = []
        for month in range(planning_horizon):
            summary.append({
                'Month': month + 1,
                'Mean_Utilization_%': np.mean(results[month]),
                'P50_Utilization_%': np.percentile(results[month], 50),
                'P85_Utilization_%': np.percentile(results[month], 85),
                'P95_Utilization_%': np.percentile(results[month], 95),
                'Prob_Overallocated_%': np.mean(np.array(results[month]) > 100)
            })
        
        return pd.DataFrame(summary)

# Example usage
# Step 1: Create estimators for different project types based on historical data
small_projects_historical = [45, 52, 48, 55, 50, 47]  # days
medium_projects_historical = [85, 92, 88, 95, 90]
large_projects_historical = [145, 160, 155, 150, 158, 162]

estimators = {
    'small': BayesianProjectEstimator(prior_mean=50, prior_std=10),
    'medium': BayesianProjectEstimator(prior_mean=90, prior_std=15),
    'large': BayesianProjectEstimator(prior_mean=150, prior_std=20)
}

# Update with historical data
estimators['small'].update_with_batch(small_projects_historical)
estimators['medium'].update_with_batch(medium_projects_historical)
estimators['large'].update_with_batch(large_projects_historical)

# Print updated estimates
for proj_type, est in estimators.items():
    mean, lower, upper = est.predict_duration(confidence_level=0.90)
    print(f"{proj_type.capitalize()} projects:")
    print(f"  Estimated duration: {mean:.1f} days (90% CI: {lower:.1f} - {upper:.1f})")
    print(f"  Probability of completing within {mean*1.2:.0f} days: "
          f"{est.probability_under_target(mean*1.2)*100:.1f}%\n")

# Step 2: Plan portfolio capacity
planner = BayesianPortfolioPlanner(estimators)

# Add projects to portfolio (convert days to months roughly)
planner.add_project('large', start_month=0, team_size=5)
planner.add_project('medium', start_month=1, team_size=3)
planner.add_project('small', start_month=2, team_size=2)
planner.add_project('large', start_month=4, team_size=5)
planner.add_project('medium', start_month=6, team_size=3)

# Simulate capacity
capacity_forecast = planner.simulate_capacity(
    total_capacity=10,  # 10 team members
    n_simulations=5000,
    planning_horizon=12
)

print("\nCapacity Forecast:")
print(capacity_forecast.to_string(index=False))
```


***

### 4. **Capacity-Based Portfolio Optimization**

Uses optimization to select and sequence projects that maximize business value while respecting resource constraints—crucial for strategic planning[^1_7][^1_8].

**When to use:** When you need to choose which projects to pursue from a candidate list, given limited resources.

**Python Implementation:**

```python
from pulp import *
import pandas as pd
import numpy as np

class PortfolioOptimizer:
    def __init__(self, projects_data):
        """
        Portfolio optimization considering capacity constraints
        
        Parameters:
        - projects_data: DataFrame with columns:
            ['project', 'value', 'duration_months', 'resource_profile', 
             'dependencies', 'mandatory']
          resource_profile: dict like {'engineers': [2,2,3,2], 'specialists': [1,1,0,1]}
        """
        self.projects = projects_data
        self.model = None
        self.selected_projects = None
        
    def optimize_portfolio(self, resource_capacity, planning_horizon, 
                          min_value_threshold=None):
        """
        Optimize project selection and scheduling
        
        Parameters:
        - resource_capacity: dict of {resource_type: capacity_per_month}
        - planning_horizon: number of months to plan
        - min_value_threshold: minimum total value to achieve
        
        Returns: optimal portfolio selection
        """
        # Create model
        self.model = LpProblem("Portfolio_Optimization", LpMaximize)
        
        n_projects = len(self.projects)
        projects = self.projects['project'].tolist()
        
        # Decision variables: select project and start month
        select = {}
        start_month = {}
        
        for i, proj in enumerate(projects):
            # Binary: select this project or not
            select[proj] = LpVariable(f"select_{proj}", cat='Binary')
            
            # Start month (if selected)
            for t in range(planning_horizon):
                start_month[proj, t] = LpVariable(
                    f"start_{proj}_{t}", cat='Binary'
                )
        
        # Objective: Maximize total value
        total_value = lpSum(
            self.projects.loc[i, 'value'] * select[proj]
            for i, proj in enumerate(projects)
        )
        self.model += total_value, "Total_Value"
        
        # Constraint 1: If selected, must start exactly once
        for proj in projects:
            self.model += (
                lpSum(start_month[proj, t] for t in range(planning_horizon)) == 
                select[proj],
                f"Start_Once_{proj}"
            )
        
        # Constraint 2: Resource capacity constraints
        for resource in resource_capacity.keys():
            for month in range(planning_horizon):
                resource_usage = []
                
                for i, proj in enumerate(projects):
                    duration = self.projects.loc[i, 'duration_months']
                    profile = self.projects.loc[i, 'resource_profile']
                    
                    if resource not in profile:
                        continue
                    
                    # Add resource usage for this project if active in this month
                    for start_t in range(planning_horizon):
                        proj_month = month - start_t
                        if 0 <= proj_month < len(profile[resource]):
                            resource_usage.append(
                                profile[resource][proj_month] * start_month[proj, start_t]
                            )
                
                if resource_usage:
                    self.model += (
                        lpSum(resource_usage) <= resource_capacity[resource],
                        f"Capacity_{resource}_Month_{month}"
                    )
        
        # Constraint 3: Dependencies
        for i, proj in enumerate(projects):
            deps = self.projects.loc[i, 'dependencies']
            if deps and deps != '-':
                dep_list = [d.strip() for d in deps.split(',')]
                for dep in dep_list:
                    if dep in projects:
                        # Dependent project must finish before this starts
                        dep_idx = projects.index(dep)
                        dep_duration = self.projects.loc[dep_idx, 'duration_months']
                        
                        for t in range(planning_horizon):
                            self.model += (
                                lpSum(start_month[proj, t2] * t2 
                                     for t2 in range(t + 1)) >=
                                lpSum(start_month[dep, t2] * (t2 + dep_duration) 
                                     for t2 in range(planning_horizon)) - 
                                (1 - select[proj]) * planning_horizon,
                                f"Dependency_{dep}_to_{proj}_time_{t}"
                            )
        
        # Constraint 4: Mandatory projects
        for i, proj in enumerate(projects):
            if self.projects.loc[i, 'mandatory']:
                self.model += select[proj] == 1, f"Mandatory_{proj}"
        
        # Constraint 5: Minimum value threshold (if specified)
        if min_value_threshold is not None:
            self.model += total_value >= min_value_threshold, "Min_Value"
        
        # Solve
        solver = PULP_CBC_CMD(msg=0, timeLimit=180)
        self.model.solve(solver)
        
        # Extract solution
        if LpStatus[self.model.status] == 'Optimal':
            self.selected_projects = []
            
            for proj in projects:
                if value(select[proj]) > 0.5:
                    start_t = None
                    for t in range(planning_horizon):
                        if value(start_month[proj, t]) > 0.5:
                            start_t = t
                            break
                    
                    proj_idx = projects.index(proj)
                    self.selected_projects.append({
                        'Project': proj,
                        'Start_Month': start_t,
                        'Duration': self.projects.loc[proj_idx, 'duration_months'],
                        'Value': self.projects.loc[proj_idx, 'value']
                    })
            
            return pd.DataFrame(self.selected_projects).sort_values('Start_Month')
        else:
            return None
    
    def get_resource_utilization(self, resource_capacity, planning_horizon):
        """Calculate resource utilization over time"""
        if self.selected_projects is None:
            return None
        
        utilization = {resource: np.zeros(planning_horizon) 
                      for resource in resource_capacity.keys()}
        
        for proj_info in self.selected_projects:
            proj = proj_info['Project']
            start = proj_info['Start_Month']
            
            # Find project data
            proj_data = self.projects[self.projects['project'] == proj].iloc[^1_0]
            profile = proj_data['resource_profile']
            
            for resource in resource_capacity.keys():
                if resource in profile:
                    for month_offset, usage in enumerate(profile[resource]):
                        month = start + month_offset
                        if month < planning_horizon:
                            utilization[resource][month] += usage
        
        # Convert to percentage
        util_df = pd.DataFrame({
            'Month': range(1, planning_horizon + 1)
        })
        
        for resource, capacity in resource_capacity.items():
            util_df[f'{resource}_Used'] = utilization[resource]
            util_df[f'{resource}_Utilization_%'] = \
                (utilization[resource] / capacity * 100).round(1)
        
        return util_df
    
    def plot_utilization(self, resource_capacity, planning_horizon):
        """Plot resource utilization"""
        util_df = self.get_resource_utilization(resource_capacity, planning_horizon)
        if util_df is None:
            return
        
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(len(resource_capacity), 1, 
                                figsize=(12, 4*len(resource_capacity)))
        
        if len(resource_capacity) == 1:
            axes = [axes]
        
        for idx, (resource, capacity) in enumerate(resource_capacity.items()):
            ax = axes[idx]
            
            months = util_df['Month']
            used = util_df[f'{resource}_Used']
            
            ax.bar(months, used, alpha=0.7, label='Used')
            ax.axhline(capacity, color='r', linestyle='--', 
                      label=f'Capacity ({capacity})')
            ax.fill_between(months, 0, capacity, alpha=0.1, color='green')
            ax.fill_between(months, capacity, used.max() * 1.1, 
                           alpha=0.1, color='red')
            
            ax.set_xlabel('Month')
            ax.set_ylabel(f'{resource.capitalize()} Count')
            ax.set_title(f'{resource.capitalize()} Utilization')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return fig

# Example usage
projects_data = pd.DataFrame([
    {
        'project': 'P1_NewProduct',
        'value': 100,
        'duration_months': 5,
        'resource_profile': {
            'engineers': [3, 4, 4, 3, 2],
            'designers': [2, 2, 1, 1, 0]
        },
        'dependencies': '-',
        'mandatory': True
    },
    {
        'project': 'P2_Optimization',
        'value': 60,
        'duration_months': 3,
        'resource_profile': {
            'engineers': [2, 3, 2],
            'designers': [0, 0, 0]
        },
        'dependencies': '-',
        'mandatory': False
    },
    {
        'project': 'P3_Integration',
        'value': 80,
        'duration_months': 4,
        'resource_profile': {
            'engineers': [2, 3, 3, 2],
            'designers': [1, 1, 1, 1]
        },
        'dependencies': 'P1_NewProduct',
        'mandatory': False
    },
    {
        'project': 'P4_Research',
        'value': 50,
        'duration_months': 6,
        'resource_profile': {
            'engineers': [1, 2, 2, 2, 1, 1],
            'designers': [1, 1, 0, 0, 0, 0]
        },
        'dependencies': '-',
        'mandatory': False
    },
    {
        'project': 'P5_Enhancement',
        'value': 40,
        'duration_months': 3,
        'resource_profile': {
            'engineers': [2, 2, 1],
            'designers': [1, 1, 1]
        },
        'dependencies': '-',
        'mandatory': False
    }
])

# Resource constraints
resource_capacity = {
    'engineers': 8,
    'designers': 3
}

# Optimize
optimizer = PortfolioOptimizer(projects_data)
optimal_portfolio = optimizer.optimize_portfolio(
    resource_capacity=resource_capacity,
    planning_horizon=12
)

print("Optimal Portfolio Selection:")
print(optimal_portfolio)
print(f"\nTotal Value: {optimal_portfolio['Value'].sum()}")

print("\nResource Utilization:")
utilization = optimizer.get_resource_utilization(resource_capacity, 12)
print(utilization)
```


***

### 5. **Scenario Planning with What-If Analysis**

Creates multiple scenarios (optimistic, likely, pessimistic, custom) to understand range of outcomes and stress-test capacity plans[^1_7][^1_9].

**When to use:** When you need to present multiple scenarios to stakeholders or stress-test your capacity plan against various assumptions.

**Python Implementation:**

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class ScenarioType(Enum):
    OPTIMISTIC = "optimistic"
    LIKELY = "likely"
    PESSIMISTIC = "pessimistic"
    CUSTOM = "custom"

@dataclass
class ProjectScenario:
    name: str
    duration_multiplier: float
    resource_multiplier: float
    new_project_probability: float
    description: str

class ScenarioPlanner:
    def __init__(self, baseline_projects):
        """
        Scenario-based capacity planning
        
        Parameters:
        - baseline_projects: DataFrame with:
            ['project', 'duration', 'monthly_resources', 'start_month', 'probability']
        """
        self.baseline = baseline_projects.copy()
        self.scenarios = self._define_standard_scenarios()
        self.results = {}
        
    def _define_standard_scenarios(self):
        """Define standard scenario assumptions"""
        return {
            ScenarioType.OPTIMISTIC: ProjectScenario(
                name="Optimistic",
                duration_multiplier=0.85,  # 15% faster
                resource_multiplier=0.90,  # 10% less resources needed
                new_project_probability=0.3,  # 30% chance of new work
                description="Best case: efficient execution, minimal scope creep"
            ),
            ScenarioType.LIKELY: ProjectScenario(
                name="Likely",
                duration_multiplier=1.0,
                resource_multiplier=1.0,
                new_project_probability=0.6,
                description="Expected case: plans executed as estimated"
            ),
            ScenarioType.PESSIMISTIC: ProjectScenario(
                name="Pessimistic",
                duration_multiplier=1.25,  # 25% longer
                resource_multiplier=1.15,  # 15% more resources
                new_project_probability=0.9,  # 90% chance of new work
                description="Worst case: delays, scope creep, resource constraints"
            )
        }
    
    def add_custom_scenario(self, name, duration_mult, resource_mult, 
                           new_proj_prob, description=""):
        """Add a custom scenario"""
        self.scenarios[name] = ProjectScenario(
            name=name,
            duration_multiplier=duration_mult,
            resource_multiplier=resource_mult,
            new_project_probability=new_proj_prob,
            description=description
        )
    
    def run_scenario(self, scenario_key, total_capacity, planning_horizon,
                    n_simulations=1000):
        """
        Run Monte Carlo simulation for a specific scenario
        
        Returns: dict with capacity statistics
        """
        scenario = self.scenarios[scenario_key]
        
        capacity_usage = []
        project_counts = []
        
        for sim in range(n_simulations):
            monthly_usage = np.zeros(planning_horizon)
            active_projects = []
            
            # Include baseline projects
            for idx, row in self.baseline.iterrows():
                # Adjust for scenario
                duration = int(np.ceil(row['duration'] * scenario.duration_multiplier))
                resources = row['monthly_resources'] * scenario.resource_multiplier
                start = row['start_month']
                
                # Add variability (±15%)
                duration_var = np.random.uniform(0.85, 1.15)
                duration = int(np.ceil(duration * duration_var))
                
                # Apply to timeline
                end = min(start + duration, planning_horizon)
                monthly_usage[start:end] += resources
                active_projects.append(row['project'])
            
            # Simulate potential new projects
            if np.random.random() < scenario.new_project_probability:
                # Random new project characteristics
                n_new = np.random.poisson(2)  # Avg 2 new projects
                
                for _ in range(n_new):
                    new_start = np.random.randint(0, planning_horizon - 2)
                    new_duration = int(np.random.uniform(2, 6))
                    new_resources = np.random.uniform(1, 4)
                    
                    end = min(new_start + new_duration, planning_horizon)
                    monthly_usage[new_start:end] += new_resources
                    active_projects.append(f"Unplanned_{sim}_{_}")
            
            capacity_usage.append(monthly_usage)
            project_counts.append(len(active_projects))
        
        # Calculate statistics
        capacity_array = np.array(capacity_usage)
        
        results = {
            'scenario': scenario.name,
            'description': scenario.description,
            'months': [],
            'mean_usage': [],
            'p50_usage': [],
            'p85_usage': [],
            'p95_usage': [],
            'prob_overallocated': [],
            'mean_utilization_%': [],
            'p85_utilization_%': []
        }
        
        for month in range(planning_horizon):
            month_usage = capacity_array[:, month]
            
            results['months'].append(month + 1)
            results['mean_usage'].append(np.mean(month_usage))
            results['p50_usage'].append(np.percentile(month_usage, 50))
            results['p85_usage'].append(np.percentile(month_usage, 85))
            results['p95_usage'].append(np.percentile(month_usage, 95))
            results['prob_overallocated'].append(
                np.mean(month_usage > total_capacity) * 100
            )
            results['mean_utilization_%'].append(
                np.mean(month_usage) / total_capacity * 100
            )
            results['p85_utilization_%'].append(
                np.percentile(month_usage, 85) / total_capacity * 100
            )
        
        # Add summary statistics
        results['avg_project_count'] = np.mean(project_counts)
        results['max_capacity_needed'] = np.percentile(capacity_array.max(axis=1), 85)
        results['months_overallocated'] = np.sum(
            np.any(capacity_array > total_capacity, axis=1)
        ) / n_simulations * 100
        
        self.results[scenario.name] = results
        return results
    
    def run_all_scenarios(self, total_capacity, planning_horizon, 
                         n_simulations=1000):
        """Run all defined scenarios"""
        for scenario_key in self.scenarios.keys():
            self.run_scenario(scenario_key, total_capacity, 
                            planning_horizon, n_simulations)
        
        return self.results
    
    def compare_scenarios(self):
        """Create comparison DataFrame across scenarios"""
        if not self.results:
            return None
        
        comparison = []
        for scenario_name, results in self.results.items():
            comparison.append({
                'Scenario': scenario_name,
                'Avg_Utilization_%': np.mean(results['mean_utilization_%']),
                'Peak_P85_Utilization_%': max(results['p85_utilization_%']),
                'Months_Risk_Overallocation_%': np.mean(results['prob_overallocated']),
                'Recommended_Capacity': int(np.ceil(results['max_capacity_needed'])),
                'Avg_Project_Count': results['avg_project_count']
            })
        
        return pd.DataFrame(comparison)
    
    def plot_scenario_comparison(self, total_capacity):
        """Plot all scenarios for comparison"""
        if not self.results:
            return
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        colors = {'Optimistic': 'green', 'Likely': 'blue', 
                 'Pessimistic': 'red'}
        
        # Plot 1: Mean utilization
        ax = axes[^1_0]
        for scenario_name, results in self.results.items():
            color = colors.get(scenario_name, 'gray')
            ax.plot(results['months'], results['mean_utilization_%'], 
                   marker='o', label=scenario_name, color=color, linewidth=2)
        
        ax.axhline(100, color='red', linestyle='--', alpha=0.5, 
                  label='100% Capacity')
        ax.axhline(85, color='orange', linestyle='--', alpha=0.5, 
                  label='85% Target')
        ax.set_xlabel('Month')
        ax.set_ylabel('Mean Utilization %')
        ax.set_title('Mean Resource Utilization by Scenario')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # Plot 2: P85 utilization (for capacity planning)
        ax = axes[^1_1]
        for scenario_name, results in self.results.items():
            color = colors.get(scenario_name, 'gray')
            months = results['months']
            p85 = results['p85_utilization_%']
            
            ax.plot(months, p85, marker='s', label=f"{scenario_name} P85",
                   color=color, linewidth=2)
            ax.fill_between(months, 0, p85, alpha=0.1, color=color)
        
        ax.axhline(100, color='red', linestyle='--', alpha=0.5)
        ax.set_xlabel('Month')
        ax.set_ylabel('P85 Utilization %')
        ax.set_title('85th Percentile Utilization (Capacity Planning Target)')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # Plot 3: Probability of overallocation
        ax = axes[^1_2]
        for scenario_name, results in self.results.items():
            color = colors.get(scenario_name, 'gray')
            ax.plot(results['months'], results['prob_overallocated'], 
                   marker='^', label=scenario_name, color=color, linewidth=2)
        
        ax.axhline(10, color='orange', linestyle='--', alpha=0.5,
                  label='10% Risk Threshold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Probability of Overallocation %')
        ax.set_title('Risk of Exceeding Capacity')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def sensitivity_analysis(self, total_capacity, planning_horizon,
                            param_name, param_range, n_simulations=500):
        """
        Analyze sensitivity to a specific parameter
        
        Parameters:
        - param_name: 'duration_multiplier' or 'resource_multiplier'
        - param_range: list of values to test
        """
        results = []
        
        for param_value in param_range:
            # Create temporary custom scenario
            if param_name == 'duration_multiplier':
                scenario_key = f"temp_{param_value}"
                self.add_custom_scenario(
                    scenario_key,
                    duration_mult=param_value,
                    resource_mult=1.0,
                    new_proj_prob=0.6,
                    description=f"Duration multiplier: {param_value}"
                )
            elif param_name == 'resource_multiplier':
                scenario_key = f"temp_{param_value}"
                self.add_custom_scenario(
                    scenario_key,
                    duration_mult=1.0,
                    resource_mult=param_value,
                    new_proj_prob=0.6,
                    description=f"Resource multiplier: {param_value}"
                )
            
            # Run scenario
            scenario_results = self.run_scenario(
                scenario_key, total_capacity, planning_horizon, n_simulations
            )
            
            results.append({
                'Parameter_Value': param_value,
                'Avg_Utilization_%': np.mean(scenario_results['mean_utilization_%']),
                'Peak_Utilization_%': max(scenario_results['p85_utilization_%']),
                'Risk_Overallocation_%': np.mean(scenario_results['prob_overallocated'])
            })
        
        return pd.DataFrame(results)

# Example usage
baseline_projects = pd.DataFrame([
    {'project': 'ProjectA', 'duration': 5, 'monthly_resources': 3, 
     'start_month': 0, 'probability': 1.0},
    {'project': 'ProjectB', 'duration': 4, 'monthly_resources': 4, 
     'start_month': 2, 'probability': 1.0},
    {'project': 'ProjectC', 'duration': 6, 'monthly_resources': 2, 
     'start_month': 4, 'probability': 0.9},
    {'project': 'ProjectD', 'duration': 3, 'monthly_resources': 3, 
     'start_month': 7, 'probability': 0.8},
])

# Initialize planner
planner = ScenarioPlanner(baseline_projects)

# Run all scenarios
total_capacity = 10  # team members
planning_horizon = 12  # months

results = planner.run_all_scenarios(
    total_capacity=total_capacity,
    planning_horizon=planning_horizon,
    n_simulations=2000
)

# Compare scenarios
comparison = planner.compare_scenarios()
print("Scenario Comparison:")
print(comparison.to_string(index=False))

# Detailed results for likely scenario
likely_results = results['Likely']
likely_df = pd.DataFrame({
    'Month': likely_results['months'],
    'Mean_Util_%': np.round(likely_results['mean_utilization_%'], 1),
    'P85_Util_%': np.round(likely_results['p85_utilization_%'], 1),
    'Risk_Overalloc_%': np.round(likely_results['prob_overallocated'], 1)
})
print("\nLikely Scenario Monthly Detail:")
print(likely_df.to_string(index=False))

# Sensitivity analysis
sensitivity = planner.sensitivity_analysis(
    total_capacity=total_capacity,
    planning_horizon=planning_horizon,
    param_name='duration_multiplier',
    param_range=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
    n_simulations=1000
)
print("\nSensitivity to Duration Estimates:")
print(sensitivity.to_string(index=False))
```


***

## Summary Comparison

| Method | Best For | Complexity | Data Requirements | Key Advantage |
| :-- | :-- | :-- | :-- | :-- |
| **PERT** | Understanding uncertainty in project timelines | Medium | Three-point estimates per task | Probabilistic completion dates |
| **RCPSP** | Resource-constrained scheduling | High | Task durations, resource needs, dependencies | Optimal resource allocation |
| **Bayesian Estimation** | Learning from historical performance | Medium | Historical project data | Self-improving estimates |
| **Portfolio Optimization** | Selecting which projects to pursue | High | Project values, resource profiles | Maximizes business value |
| **Scenario Planning** | Stress-testing capacity plans | Medium | Baseline projects, assumptions | Multiple future views |

Each method addresses different aspects of your capacity planning challenge. I'd recommend starting with **PERT** (simplest upgrade from basic Monte Carlo) and **Scenario Planning** (great for stakeholder communication), then adding **Bayesian Estimation** as you accumulate more historical data, and finally **RCPSP** or **Portfolio Optimization** when you need to make hard trade-off decisions about resource allocation or project selection.
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30]</span>

<div align="center">⁂</div>

[^1_1]: https://www.youtube.com/watch?v=LMy8cGdzCMg

[^1_2]: https://www.linkedin.com/pulse/critical-path-method-cpm-project-management-python-yustian-ekky-mkcfc

[^1_3]: https://stackoverflow.com/questions/72843244/resource-constrained-scheduling-project-using-pyschedule

[^1_4]: https://python.plainenglish.io/solving-the-resource-constrained-project-scheduling-problem-rcpsp-with-python-and-pyomo-001cffd5344a

[^1_5]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10965238/

[^1_6]: https://www.pmi.org/learning/library/estimating-minimize-loss-bayesian-theory-4868

[^1_7]: https://planisware.com/resources/resource-management-capacity-planning/complete-2026-guide-resource-management-projects

[^1_8]: https://www.epicflow.com/blog/resource-capacity-planning-what-why-and-how/

[^1_9]: https://triskellsoftware.com/blog/project-portfolio-management-trends/

[^1_10]: https://www.epicflow.com/blog/4-tips-on-efficient-resource-allocation-in-a-multi-project-environment/

[^1_11]: https://www.celoxis.com/article/best-capacity-planning-tools

[^1_12]: https://www.projectmanager.com/blog/project-scheduling-techniques

[^1_13]: https://www.machinelearningmastery.com/how-to-score-probability-predictions-in-python/

[^1_14]: https://www.tempo.io/blog/resource-allocation-in-project-management

[^1_15]: https://pkghosh.wordpress.com/2020/05/11/monte-carlo-simulation-library-in-python-with-project-cost-estimation-as-an-example/

[^1_16]: https://www.theprojectgroup.com/blog/en/capacity-planning-in-project-management/

[^1_17]: https://plane.so/blog/resource-scheduling-in-project-management-how-it-works

[^1_18]: https://www.geeksforgeeks.org/python/estimating-pi-with-buffons-needle-in-python/

[^1_19]: https://www.ecisolutions.com/blog/distribution/khameleon/resource-scheduling-101-key-things-to-consider/

[^1_20]: https://www.pymc.io/blog/chris_F_pydata2022.html

[^1_21]: https://www.youtube.com/watch?v=UXPeO2d9nSs

[^1_22]: https://www.sciencedirect.com/topics/mathematics/bayesian-estimation

[^1_23]: https://ijsr.internationaljournallabs.com/index.php/ijsr/article/view/2674

[^1_24]: https://www.hexaly.com/templates/resource-constrained-project-scheduling-problem-rcpsp

[^1_25]: https://www.youtube.com/watch?v=H3SEEhkjJMY

[^1_26]: https://www.mitre.org/sites/default/files/pdf/05_0211.pdf

[^1_27]: https://github.com/cevateness/project_scheduling

[^1_28]: https://github.com/arora-amit37/project_management_cpm_pert

[^1_29]: https://en.wikipedia.org/wiki/Bayes_estimator

[^1_30]: https://www.sciencedirect.com/science/article/pii/S0377221724008269

