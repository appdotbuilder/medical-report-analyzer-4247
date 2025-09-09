from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


class TestStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REVIEWED = "reviewed"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AgeGroup(str, Enum):
    CHILD = "child"  # 0-12
    TEEN = "teen"  # 13-19
    ADULT = "adult"  # 20-64
    SENIOR = "senior"  # 65+


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    date_of_birth: Optional[datetime] = Field(default=None)
    gender: Optional[Gender] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    test_reports: List["TestReport"] = Relationship(back_populates="user")


class TestType(SQLModel, table=True):
    __tablename__ = "test_types"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)  # e.g., "Blood Test", "Hormone Panel"
    description: str = Field(default="", max_length=500)
    category: str = Field(max_length=50)  # e.g., "Blood", "Hormone", "Metabolic"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    test_parameters: List["TestParameter"] = Relationship(back_populates="test_type")
    test_reports: List["TestReport"] = Relationship(back_populates="test_type")


class TestParameter(SQLModel, table=True):
    __tablename__ = "test_parameters"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    test_type_id: int = Field(foreign_key="test_types.id")
    name: str = Field(max_length=100)  # e.g., "Testosterone", "Hemoglobin"
    code: str = Field(max_length=20)  # e.g., "TST", "HGB"
    unit: str = Field(max_length=20)  # e.g., "ng/dL", "g/dL"
    description: str = Field(default="", max_length=300)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    test_type: TestType = Relationship(back_populates="test_parameters")
    reference_ranges: List["ReferenceRange"] = Relationship(back_populates="test_parameter")
    test_results: List["TestResult"] = Relationship(back_populates="test_parameter")


class ReferenceRange(SQLModel, table=True):
    __tablename__ = "reference_ranges"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    test_parameter_id: int = Field(foreign_key="test_parameters.id")
    gender: Optional[Gender] = Field(default=None)  # None means applies to all genders
    age_group: Optional[AgeGroup] = Field(default=None)  # None means applies to all ages
    min_age: Optional[int] = Field(default=None)  # Specific age range (optional)
    max_age: Optional[int] = Field(default=None)  # Specific age range (optional)
    min_value: Optional[Decimal] = Field(default=None, decimal_places=3)
    max_value: Optional[Decimal] = Field(default=None, decimal_places=3)
    optimal_min: Optional[Decimal] = Field(default=None, decimal_places=3)  # Optimal range
    optimal_max: Optional[Decimal] = Field(default=None, decimal_places=3)  # Optimal range
    notes: str = Field(default="", max_length=300)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    test_parameter: TestParameter = Relationship(back_populates="reference_ranges")


class TestReport(SQLModel, table=True):
    __tablename__ = "test_reports"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    test_type_id: int = Field(foreign_key="test_types.id")
    report_name: str = Field(max_length=200)  # User-defined name for the report
    test_date: datetime = Field()  # When the test was actually performed
    lab_name: str = Field(default="", max_length=100)  # Laboratory name
    doctor_name: str = Field(default="", max_length=100)  # Ordering physician
    status: TestStatus = Field(default=TestStatus.PENDING)
    notes: str = Field(default="", max_length=1000)  # User or doctor notes
    file_path: Optional[str] = Field(default=None, max_length=500)  # Path to uploaded file
    file_name: Optional[str] = Field(default=None, max_length=255)  # Original filename
    extra_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Additional metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="test_reports")
    test_type: TestType = Relationship(back_populates="test_reports")
    test_results: List["TestResult"] = Relationship(back_populates="test_report")


class TestResult(SQLModel, table=True):
    __tablename__ = "test_results"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    test_report_id: int = Field(foreign_key="test_reports.id")
    test_parameter_id: int = Field(foreign_key="test_parameters.id")
    value: Decimal = Field(decimal_places=3)  # The actual test result value
    is_abnormal: bool = Field(default=False)  # Flagged as abnormal by lab
    abnormal_flag: Optional[str] = Field(default=None, max_length=10)  # H, L, HH, LL, etc.
    notes: str = Field(default="", max_length=300)  # Notes specific to this result
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    test_report: TestReport = Relationship(back_populates="test_results")
    test_parameter: TestParameter = Relationship(back_populates="test_results")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255)
    date_of_birth: Optional[datetime] = Field(default=None)
    gender: Optional[Gender] = Field(default=None)


class UserUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    date_of_birth: Optional[datetime] = Field(default=None)
    gender: Optional[Gender] = Field(default=None)


class TestTypeCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    category: str = Field(max_length=50)


class TestParameterCreate(SQLModel, table=False):
    test_type_id: int
    name: str = Field(max_length=100)
    code: str = Field(max_length=20)
    unit: str = Field(max_length=20)
    description: str = Field(default="", max_length=300)


class ReferenceRangeCreate(SQLModel, table=False):
    test_parameter_id: int
    gender: Optional[Gender] = Field(default=None)
    age_group: Optional[AgeGroup] = Field(default=None)
    min_age: Optional[int] = Field(default=None)
    max_age: Optional[int] = Field(default=None)
    min_value: Optional[Decimal] = Field(default=None, decimal_places=3)
    max_value: Optional[Decimal] = Field(default=None, decimal_places=3)
    optimal_min: Optional[Decimal] = Field(default=None, decimal_places=3)
    optimal_max: Optional[Decimal] = Field(default=None, decimal_places=3)
    notes: str = Field(default="", max_length=300)


class TestReportCreate(SQLModel, table=False):
    user_id: int
    test_type_id: int
    report_name: str = Field(max_length=200)
    test_date: datetime
    lab_name: str = Field(default="", max_length=100)
    doctor_name: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=1000)


class TestReportUpdate(SQLModel, table=False):
    report_name: Optional[str] = Field(default=None, max_length=200)
    lab_name: Optional[str] = Field(default=None, max_length=100)
    doctor_name: Optional[str] = Field(default=None, max_length=100)
    status: Optional[TestStatus] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)


class TestResultCreate(SQLModel, table=False):
    test_report_id: int
    test_parameter_id: int
    value: Decimal = Field(decimal_places=3)
    is_abnormal: bool = Field(default=False)
    abnormal_flag: Optional[str] = Field(default=None, max_length=10)
    notes: str = Field(default="", max_length=300)


class TestResultUpdate(SQLModel, table=False):
    value: Optional[Decimal] = Field(default=None, decimal_places=3)
    is_abnormal: Optional[bool] = Field(default=None)
    abnormal_flag: Optional[str] = Field(default=None, max_length=10)
    notes: Optional[str] = Field(default=None, max_length=300)


# Response schemas for data visualization and analysis
class TestResultWithRange(SQLModel, table=False):
    result_id: int
    parameter_name: str
    parameter_code: str
    unit: str
    value: Decimal
    is_abnormal: bool
    abnormal_flag: Optional[str]
    reference_min: Optional[Decimal]
    reference_max: Optional[Decimal]
    optimal_min: Optional[Decimal]
    optimal_max: Optional[Decimal]
    status: str  # "normal", "low", "high", "optimal"
    notes: str


class TestReportSummary(SQLModel, table=False):
    report_id: int
    report_name: str
    test_type_name: str
    test_date: datetime
    lab_name: str
    status: TestStatus
    total_parameters: int
    abnormal_count: int
    normal_count: int
    results: List[TestResultWithRange]


class TrendData(SQLModel, table=False):
    parameter_name: str
    parameter_code: str
    unit: str
    data_points: List[Dict[str, Any]]  # [{date, value, is_abnormal}, ...]
    reference_min: Optional[Decimal]
    reference_max: Optional[Decimal]
    optimal_min: Optional[Decimal]
    optimal_max: Optional[Decimal]
