CREATE TABLE "User" (
    userId SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    passwordHash VARCHAR(255) NOT NULL
);

CREATE TABLE "Course" (
    courseId SERIAL PRIMARY KEY,
    userId INT REFERENCES "User"(userId) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    instructor VARCHAR(100),
    term VARCHAR(50)
);

CREATE TABLE "Assignment" (
    assignmentId SERIAL PRIMARY KEY,
    courseId INT REFERENCES "Course"(courseId) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    dueDate DATE,
    status VARCHAR(50),
    difficulty VARCHAR(50),
    estimatedHours FLOAT
);

CREATE TABLE "Material" (
    materialId SERIAL PRIMARY KEY,
    courseId INT REFERENCES "Course"(courseId) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    filepath VARCHAR(255)
);

CREATE TABLE "Tag" (
    tagId SERIAL PRIMARY KEY,
    userId INT REFERENCES "User"(userId) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    UNIQUE(userId, name)
);

CREATE TABLE "AssignmentTag" (
    assignmentId INT REFERENCES "Assignment"(assignmentId) ON DELETE CASCADE,
    tagId INT REFERENCES "Tag"(tagId) ON DELETE CASCADE,
    PRIMARY KEY (assignmentId, tagId)
);
